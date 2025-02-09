package sa.com.demaenergy.energymonitor;

import akka.actor.typed.ActorRef;
import akka.actor.typed.ActorSystem;
import akka.actor.typed.Behavior;
import akka.actor.typed.Scheduler;
import akka.actor.typed.javadsl.*;
import akka.http.javadsl.Http;
import akka.http.javadsl.ServerBinding;
import akka.http.javadsl.marshallers.jackson.Jackson;
import akka.http.javadsl.server.Route;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import sa.com.demaenergy.db.EnergyMonitorRepo;
import sa.com.demaenergy.energymonitor.model.Dam;
import static akka.http.javadsl.server.Directives.*;
import static java.time.LocalDateTime.now;

import akka.http.javadsl.model.StatusCodes;
import sa.com.demaenergy.energymonitor.model.DamRequest;

import java.net.InetSocketAddress;
import java.sql.Timestamp;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.CompletionStage;

public class DayAheadMarket extends AbstractBehavior<DayAheadMarket.Command> {

    private final ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo;
    private final SimpleDateFormat inputFormat;
    private final SimpleDateFormat outputFormat;
    public DayAheadMarket(ActorContext<Command> context, ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo) {
        super(context);
        this.energyMonitorRepo = energyMonitorRepo;
        inputFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        inputFormat.setTimeZone(TimeZone.getTimeZone("US/Central"));
        outputFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        outputFormat.setTimeZone(TimeZone.getTimeZone("Asia/Riyadh"));
        DamHTTP htp = new DamHTTP(getContext().getSystem(), getContext().getSelf());
        htp.startHttpServer(htp.damRoutes(), getContext().getSystem());
    }

    public sealed interface Command {
    }

    public record DAMPrice(ActorRef<DAMSubscriber> replyTo) implements Command {
    }
    public record DAMSubscriber(Dam damPrice) implements Command {
    }
    private record RespondToDAMSubscriber(ActorRef<DAMSubscriber> replyTo, Dam damPrice) implements Command {
    }
    private record RespondToDAMSubscriberFailure(Throwable th) implements Command {
    }
    public record SubmitDAMtoDB(ActorRef<SubmitDamResponse> replyTo, List<DamRequest.damPurchase> dam) implements Command {
    }
    public record SubmitDamResponse(String status) implements Command {
    }

    private Behavior<Command> fetchDAMPrice(DAMPrice command) {
        getContext().ask(EnergyMonitorRepo.Message.Response.DAMPriceResponse.class,
                energyMonitorRepo,
                Duration.ofSeconds(2),
                EnergyMonitorRepo.Message.GetDAMPrice::new,
                (response, th) -> {
                    if (response != null) {
                        return new RespondToDAMSubscriber(command.replyTo, response.dam());
                    } else {
                        return new RespondToDAMSubscriberFailure(th);
                    }
                });
        return Behaviors.same();
    }

    private Behavior<Command> respondToDAMSubscriber(RespondToDAMSubscriber command) {
        command.replyTo.tell(new DAMSubscriber(command.damPrice));
        return Behaviors.same();
    }

    private Behavior<Command> respondToDAMSubscriberFailure(RespondToDAMSubscriberFailure command) {
        getContext().getLog().error("Failed to fetch DAM price", command.th);
        return Behaviors.same();
    }

    private Behavior<Command> submitDAMtoDB(SubmitDAMtoDB command) {
        try {
            for(DamRequest.damPurchase damPurchase: command.dam()) {
                getContext().getLog().info("DAM Purchase: {}", damPurchase);
                Date startTime = inputFormat.parse(STR."\{damPurchase.tradingDate()} \{damPurchase.startTime()}");
                Date endTime = inputFormat.parse(STR."\{damPurchase.tradingDate()} \{damPurchase.endTime()}");

                Dam dam = new Dam(UUID.randomUUID().toString(), damPurchase.bidID(),
                        Timestamp.valueOf(outputFormat.format(startTime)),
                        Timestamp.valueOf(outputFormat.format(endTime)), damPurchase.settlementPoint(),
                        damPurchase.awardedMwh(), damPurchase.spp(), Timestamp.valueOf(now()));
                energyMonitorRepo.tell(new EnergyMonitorRepo.Message.SaveDAMPrice(dam)); // TODO end time is skipping day
            }
            command.replyTo().tell(new SubmitDamResponse("WE COOL"));

        } catch (ParseException e) {
            getContext().getLog().error("Failed to parse date", e);
        }
        return Behaviors.same();
    }

    public static Behavior<Command> create(ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo) {
        return Behaviors.setup(context -> new DayAheadMarket(context, energyMonitorRepo));
    }

    private static class DamHTTP {
        private final static Logger log = LoggerFactory.getLogger(DamHTTP.class);
        private final ActorRef<DayAheadMarket.Command> dayAheadMarket;
        private final Duration askTimeout;
        private final Scheduler scheduler;
        private DamHTTP(ActorSystem<?> system, ActorRef<Command> dayAheadMarket) {
            this.dayAheadMarket = dayAheadMarket;
            scheduler = system.scheduler();
            askTimeout = Duration.ofSeconds(2);
        }

        private CompletionStage<DayAheadMarket.SubmitDamResponse> loadDAMPrice(List<DamRequest.damPurchase> dam) {
            return AskPattern.ask(dayAheadMarket, ref -> new SubmitDAMtoDB(ref, dam), askTimeout, scheduler);
        }

        Route damRoutes() {
            return pathPrefix("dam", () ->
                concat(
                    pathEnd(() ->
                        concat(
                            post(() ->
                                entity(
                                    Jackson.unmarshaller(DamRequest.class),
                                    dam -> {
                                        log.info("Received DAM request: {}", dam);
                                        CompletionStage<DayAheadMarket.SubmitDamResponse> futureResponse = loadDAMPrice(dam.damPurchase());
                                        return onSuccess(() -> futureResponse, response -> complete(StatusCodes.OK, response.status)
                                        );
                                    }
                                )
                            )
                        )
                    )
                )
            );
        }
        void startHttpServer(Route route, ActorSystem<?> system) {
            CompletionStage<ServerBinding> futureBinding =
                    Http.get(system).newServerAt("localhost", 8080).bind(route);

            futureBinding.whenComplete((binding, exception) -> {
                if (binding != null) {
                    InetSocketAddress address = binding.localAddress();
                    system.log().info("Server online at http://{}:{}/",
                            address.getHostString(),
                            address.getPort());
                } else {
                    system.log().error("Failed to bind HTTP endpoint, terminating system", exception);
                    system.terminate();
                }
            });
        }
    }

    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
                .onMessage(DAMPrice.class, this::fetchDAMPrice)
                .onMessage(RespondToDAMSubscriber.class, this::respondToDAMSubscriber)
                .onMessage(RespondToDAMSubscriberFailure.class, this::respondToDAMSubscriberFailure)
                .onMessage(SubmitDAMtoDB.class, this::submitDAMtoDB)
                .build();
    }
}
