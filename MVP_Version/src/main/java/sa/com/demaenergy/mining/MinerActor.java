package sa.com.demaenergy.mining;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.*;
import akka.http.javadsl.Http;
import akka.http.javadsl.model.*;
import akka.http.javadsl.model.headers.Authorization;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import sa.com.demaenergy.mining.manager.MinersController;
import sa.com.demaenergy.mining.model.MinerSummaryRequest;
import sa.com.demaenergy.mining.model.TokenRequest;

import java.net.URI;
import java.net.http.HttpClient;
import java.util.List;
import java.util.concurrent.*;

import static java.net.http.HttpRequest.newBuilder;
import static java.util.concurrent.TimeUnit.SECONDS;

public class MinerActor extends AbstractBehavior<MinerActor.Command> {
    private final Http http = Http.get(getContext().getSystem());

    private final ActorRef<MinersController.Message> miningController;

    private final String id;
    private final String ip;
    private final int port;
    private final String password;
    private String token;
    private final ObjectMapper mapper;
    private MinerState state = MinerState.INITIALIZING;


    public sealed interface Command {
    }

    public record Restart(ActorRef<MinersController.Message> replyTo) implements Command {
    }

    public record Reboot(ActorRef<MinersController.Message> replyTo) implements Command {
    }

    public record Start(ActorRef<MinersController.Message> replyTo) implements Command {
    }

    public record Pause(ActorRef<MinersController.Message> replyTo) implements Command {
    }

    public record Resume(ActorRef<MinersController.Message> replyTo) implements Command {
    }

    public record Stop(ActorRef<MinersController.Message> replyTo) implements Command {
    }

    public record Summary() implements Command {
    }

    private record Auth(Command cmd) implements Command {
    }

    private record AuthSuccess(HttpResponse httpResponse, Command cmd) implements Command {
    }

    private record AuthFailure(Throwable th) implements Command {
    }

    private record MinerFailure(Throwable th, HttpResponse httpResponse, Command command) implements Command {
    }

    private record MinerSuccess(HttpResponse httpResponse) implements Command {
    }


    private record MonitorStateResponse(HttpResponse httpResponse) implements Command {
    }

    public MinerActor(ActorContext<Command> context, String id, String ip, int port, String password, TimerScheduler<Command> timers, ActorRef<MinersController.Message> miningController) {
        super(context);
        this.id = id;
        this.ip = ip;
        this.port = port;
        this.password = password;
        mapper = new ObjectMapper();
        this.miningController = miningController;
    }

    private Behavior<Command> auth(Auth command) {
        String url = STR."http://\{ip}:\{port}/api/v1/unlock";
        String payLoad = STR."{\"pw\": \"\{password}\"}";

        CompletionStage<HttpResponse> response = http.singleRequest(HttpRequest.POST(url)
                .withEntity(HttpEntities.create(ContentTypes.APPLICATION_JSON, payLoad)));

        getContext().pipeToSelf(response, (httpResponse, th) -> {
            if (th != null) {
                return new AuthFailure(th);
            } else {
                return new AuthSuccess(httpResponse, command.cmd);
            }
        });

        return Behaviors.same();
    }

    private Behavior<Command> authSuccess(AuthSuccess command) {
        CompletionStage<String> stringCompletionStage = command.httpResponse.entity()
                .toStrict(1000, getContext().getSystem())
                .thenApply(strict -> strict.getData().utf8String());
        stringCompletionStage.thenAccept(token -> {
            try {
                TokenRequest tokenRequest = mapper.readerFor(TokenRequest.class).readValue(token);
                getContext().getLog().info("Token: {}", tokenRequest.toString());
                this.token = tokenRequest.token();
            } catch (JsonProcessingException e) {
                getContext().getLog().error("Failed to deserialize token", e);
            }
            switch (command.cmd) {
                case Restart restart -> getContext().getSelf().tell(restart);
                case Reboot reboot -> getContext().getSelf().tell(reboot);
                case Start start -> getContext().getSelf().tell(start);
                case Pause pause -> getContext().getSelf().tell(pause);
                case Resume resume -> getContext().getSelf().tell(resume);
                case Summary summary -> getContext().getSelf().tell(summary);
                default -> getContext().getLog().error(STR."Unexpected command: \{command.cmd}");
            }
        });

        return Behaviors.same();
    }

    private Behavior<Command> authFailure(AuthFailure command) {
        getContext().getLog().error("Failed to authenticate", command.th);
        return Behaviors.same();
    }

    public Behavior<Command> restart(Restart command) {
        getContext().getLog().info("Restarting miner with id: {}", id);
        var cmd = "mining/restart";
        CompletionStage<HttpResponse> request = postRequest(cmd);
        return pipeFuture(request, command);
    }


    public Behavior<Command> reboot(Reboot command) {
        getContext().getLog().info("Rebooting miner with id: {}", id);
        var cmd = "system/reboot";
        CompletionStage<HttpResponse> request = postRequest(cmd);

        return pipeFuture(request, command);
    }

    public Behavior<Command> start(Start command) {
        if (state == MinerState.MINING) {
            getContext().getLog().info("Miner with id: {} is already mining", id);
//            command.replyTo.tell(new MinersController.Message.MinerReport(id, state));
            return Behaviors.same();
        }
        getContext().getLog().info("Starting miner with id: {}", id);
        var cmd = "mining/start";
        CompletionStage<HttpResponse> request = postRequest(cmd);
        return pipeFuture(request, command);
    }


    public Behavior<Command> pause(Pause command) {
        if (state == MinerState.STOPPED) {
            getContext().getLog().info("Miner with id: {} is already paused", id);
//            command.replyTo.tell(new MinersController.Message.MinerReport(id, state));
            return Behaviors.same();
        }
        getContext().getLog().info("Pausing miner with id: {}", id);
        var cmd = "mining/pause";
        CompletionStage<HttpResponse> request = postRequest(cmd);
        return pipeFuture(request, command);
    }


    public Behavior<Command> resume(Resume command) {
        if (state == MinerState.MINING) {
            getContext().getLog().info("Miner with id: {} is already mining", id);
//            command.replyTo.tell(new MinersController.Message.MinerReport(id, state));
            return Behaviors.same();
        }
        getContext().getLog().info("Resuming miner with id: {}", id);
        var cmd = "mining/resume";
        CompletionStage<HttpResponse> request = postRequest(cmd);
        return pipeFuture(request, command);
    }

    public Behavior<Command> summary(Summary command) {
        getContext().getLog().info("getting summary for miner: {}", id);
        Logger log = getContext().getLog();
        var cmd = "summary";
        CompletionStage<HttpResponse> request = getRequest(cmd);
        return pipeFuture(request.toCompletableFuture()
                .orTimeout(20L, SECONDS), command);
    }

    private Behavior<Command> pipeFuture(CompletionStage<HttpResponse> future, Command command) {
        getContext().pipeToSelf(future, (httpResponse, th) -> {
            if (th != null) {
                return new MinerFailure(th, httpResponse, command);
            }
            if (httpResponse.status().intValue() == 401) {
                return new Auth(command);
            } else if (httpResponse.status().isFailure()) {
                return new MinerFailure(th, httpResponse, command);
            } else {
                if (command instanceof Summary) {
                    return new MonitorStateResponse(httpResponse);
                }
                return new MinerSuccess(httpResponse);
            }
        });
        return Behaviors.same();
    }

    private CompletionStage<HttpResponse> postRequest(String cmd) {
        String url = STR."http://\{ip}:\{port}/api/v1/\{cmd}";
        List<HttpHeader> headers = List.of(Authorization.
                parse("Authorization", String.format("%s", token)));
        return http.singleRequest(HttpRequest.POST(url)
                .withHeaders(headers));
    }

    private CompletionStage<HttpResponse> getRequest(String cmd) {
        getContext().getLog().info("Getting request for: {}", cmd);
        String url = STR."http://\{ip}:\{port}/api/v1/\{cmd}";
        List<HttpHeader> headers = List.of(Authorization.
                parse("Authorization", String.format("%s", token)));
        return http.singleRequest(HttpRequest.GET(url)
                .withHeaders(headers));
    }

    private Behavior<Command> minerFailure(MinerFailure command) {
        getContext().getLog().error("Failed to execute command : {}, Exception: ", command.command, command.th);

        if (command.command instanceof Summary) {
            miningController.tell(new MinersController.Message.MinerSummary(id,
                    new MinerSummaryRequest.MinerSummary(
                            new MinerSummaryRequest.MinerSummary.MinerStatus("FAILURE", 0),
                            "UNKNOWN",
                            -1.0,
                            -1.0,
                            -1.0,
                            -1.0,
                            -1,
                            -1,
                            -1.0,
                            new MinerSummaryRequest.MinerSummary.ChipTemp(-1, -1),
                            new MinerSummaryRequest.MinerSummary.PcbTemp(-1, -1)
                    ),
                    null));
            return Behaviors.same();
        } else {
            getContext().getLog().error("the miner failure is not handled for command: {} ", command.command);
        }

        return Behaviors.same();
    }

    private Behavior<Command> minerSuccess(MinerSuccess command) {
        CompletionStage<String> stringCompletionStage = command.httpResponse.entity()
                .toStrict(1000, getContext().getSystem())
                .thenApply(strict -> strict.getData().utf8String());
        stringCompletionStage.thenAccept(r ->
                getContext().getLog().info("Command executed successfully with response: {}", r)
        );
        return Behaviors.same();
    }

    private Behavior<Command> minerStateResponse(MonitorStateResponse command) {
        getContext().getLog().info("Received response for miner state: {}", id);
        CompletionStage<String> stringCompletionStage = command.httpResponse.entity()
                .toStrict(1000, getContext().getSystem())
                .thenApply(strict -> strict.getData().utf8String());

        String tempMetricDataBlocking = getTempMetricDataBlocking();

        final MinersController.Message.MinerSummary minerNotRespondingSummary = new MinersController.Message.MinerSummary(id,
                new MinerSummaryRequest.MinerSummary(
                        new MinerSummaryRequest.MinerSummary.MinerStatus("FAILURE", 0),
                        "UNKNOWN",
                        -1.0,
                        -1.0,
                        -1.0,
                        -1.0,
                        -1,
                        -1,
                        -1.0,
                        new MinerSummaryRequest.MinerSummary.ChipTemp(-1, -1),
                        new MinerSummaryRequest.MinerSummary.PcbTemp(-1, -1)
                ),
                tempMetricDataBlocking);
        try {
//            TODO: baaaaaaad, don't block the thread!!!!
            String summary = stringCompletionStage.toCompletableFuture().get(4L, SECONDS);
            MinerSummaryRequest minerSummaryRequest = mapper
                    .readerFor(MinerSummaryRequest.class).readValue(summary);

            if (minerSummaryRequest.minerSummary() == null) {
                getContext().getLog().error("Miner: {} summary is null", id);
                miningController.tell(minerNotRespondingSummary
                );
                return Behaviors.same();
            }
            state = MinerState.valueOf(minerSummaryRequest.minerSummary()
                    .minerStatus().minerState().toUpperCase());
            getContext().getLog().info("Miner: {} updated state {}", id, state);
            miningController.tell(new MinersController.Message.MinerSummary(id, minerSummaryRequest.minerSummary(), tempMetricDataBlocking));
        } catch (CancellationException | CompletionException | JsonProcessingException e) {
            getContext().getLog().error("Failed to deserialize miner state", e);
        } catch (ExecutionException | InterruptedException e) {
            throw new RuntimeException(e);
        } catch (TimeoutException e) {
            miningController.tell(minerNotRespondingSummary);
            throw new RuntimeException(e);
        }
        return Behaviors.same();
    }

    private String getTempMetricDataBlocking() {
        try (HttpClient httpClient = HttpClient.newHttpClient()) {
            java.net.http.HttpRequest build = newBuilder().GET()
                    .uri(URI.create(STR."http://\{ip}:\{port}/api/v1/metrics?time_slice=3600&step=60"))
                    .build();
            Logger log = getContext().getLog();
            return httpClient.sendAsync(build, java.net.http.HttpResponse.BodyHandlers.ofString())
                    .thenApply(response -> {
                        if (response.statusCode() == 200) {
                            log.debug(STR."Temp metric data: \{response.body()}");
                            return response.body();
                        } else {
                            log.error(STR."Failed to get temp metric data: \{response.body()}");
                            return null;
                        }
                    })
                    .exceptionally(ex -> {
                        log.error(STR."Failed to get temp metric data: \{ex.getMessage()}");
                        return null;
                    })
//                    TODO: Bad baaad!!!!!
                    .get(10, SECONDS);


        } catch (ExecutionException | InterruptedException e) {
            getContext().getLog().error("Failed to get temp metric data", e);
        } catch (TimeoutException e) {
            getContext().getLog().error("Failed to get temp metric data", e);
        }
        return null;
    }


    public static Behavior<Command> create(String id, String ip, int port,
                                           String password, ActorRef<MinersController.Message> miningController) {
        return Behaviors.withTimers(timers -> Behaviors.setup(ctx ->
                new MinerActor(ctx, id, ip, port, password, timers, miningController)));
    }

    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
                .onMessage(Reboot.class, this::reboot)
                .onMessage(Restart.class, this::restart)
                .onMessage(Start.class, this::start)
                .onMessage(Pause.class, this::pause)
                .onMessage(Resume.class, this::resume)
                .onMessage(Summary.class, this::summary)
                .onMessage(Auth.class, this::auth)
                .onMessage(AuthSuccess.class, this::authSuccess)
                .onMessage(AuthFailure.class, this::authFailure)
                .onMessage(MinerFailure.class, this::minerFailure)
                .onMessage(MinerSuccess.class, this::minerSuccess)
                .onMessage(MonitorStateResponse.class, this::minerStateResponse)
                .build();
    }

    public enum MinerState {
        MINING,
        STARTING,
        INITIALIZING,
        STOPPED,
        RESTARTING,
        FAILURE
    }
}
