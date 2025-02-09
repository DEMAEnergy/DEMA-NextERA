package sa.com.demaenergy.energymonitor;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.*;
import akka.http.javadsl.Http;
import akka.http.javadsl.model.*;
import akka.http.javadsl.model.headers.Authorization;
import akka.util.ByteString;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectReader;
import sa.com.demaenergy.db.EnergyMonitorRepo;
import sa.com.demaenergy.energymonitor.model.EmergencyEventResponse;
import sa.com.demaenergy.energymonitor.model.EmergencyEventResponse.EmergencyEvent;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.CompletionStage;


public class EmergencyResponse extends AbstractBehavior<EmergencyResponse.Command> {
    private final ObjectReader reader;
    private final ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo;
    private final Http http = Http.get(getContext().getSystem());
    private String apiKey;
    private String apiPath;
    private String apiCommand;
    int apiID = getContext().getSystem().settings().config().getInt("ercot.api-id"); //todo: should be taken from database

    private final String companyID = getContext().getSystem().settings().config().getString("company-id");
    private EmergencyEvent emergencyEvent;

    public sealed interface Command {}

    public record EmergencyState(ActorRef<EnergyMonitor.Command> replyTo, UUID requestID) implements Command {}
    private record EmergencyRequestSuccess(HttpResponse httpResponse) implements Command {
    }
    private record DeserializeEmergencyEvent(String emergencyEventResponse) implements Command {
    }
    private record EmergencyRequestFailure(Throwable th) implements Command {
    }
    private record FetchEmergencyEvent(ActorRef<Command> replyTo) implements Command {}
    private record FetchAPI(EnergyMonitorRepo.Message.Response.APIResponse response) implements Command {}

    private EmergencyResponse(ActorContext<Command> context,
                              ObjectReader reader, ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo) {
        super(context);
        this.reader = reader;
        this.energyMonitorRepo = energyMonitorRepo;
        ActorRef<EnergyMonitorRepo.Message.Response.APIResponse> apiResponseActor = context.messageAdapter(EnergyMonitorRepo.Message.Response.APIResponse.class,
                FetchAPI::new
        );
        this.energyMonitorRepo.tell(new EnergyMonitorRepo.Message.GetAPI(apiResponseActor, apiID));
        getContext().getLog().info("Fetching emergency event API");
    }

    private Behavior<Command> fetchEmergencyEvent(FetchEmergencyEvent command) {
        getContext().getLog().info(apiCommand);
        getContext().getLog().info("Fetching emergency event");
        List<HttpHeader> headers = List.of(Authorization.
                parse("Authorization", String.format("Basic %s", apiKey)));
        String payLoad ="command=%s&a={\"companypid\":\"%s\"}".formatted(apiCommand, companyID);

        CompletionStage<HttpResponse> request = http.singleRequest(HttpRequest
                .POST(apiPath).withHeaders(headers)
                .withEntity(HttpEntities.create(ContentTypes.APPLICATION_X_WWW_FORM_URLENCODED, payLoad)));

        getContext().pipeToSelf(request, (httpResponse, th) -> {
            if (th != null) {
                return new EmergencyRequestFailure(th);
            } else {
                return new EmergencyRequestSuccess(httpResponse);
            }
        });
        return Behaviors.same();
    }

    private Behavior<Command> parseEmergencyEvent(EmergencyRequestSuccess command) {
        getContext().getLog().info("Emergency event fetched successfully");

        List<String> tempEmergencyEvent = new ArrayList<>();

        command.httpResponse.entity().getDataBytes()
                .map(ByteString::utf8String)
                .runForeach(tempEmergencyEvent::add, getContext().getSystem())
                .thenAccept(done -> getContext().getSelf().tell(new DeserializeEmergencyEvent(tempEmergencyEvent.getFirst())));

        return Behaviors.same();
    }

    private Behavior<Command> handleRequestFailure(EmergencyRequestFailure command) {
        getContext().getLog().error("Error fetching emergency event: {}", command.th.getMessage());
        return Behaviors.same();
    }

    private Behavior<Command> emergencyState(EmergencyState command) {
        command.replyTo.tell(new EnergyMonitor.EmergencyStateResponse(emergencyEvent, command.requestID));
        return Behaviors.same();
    }
    private Behavior<Command> deserializeEmergencyEvent(DeserializeEmergencyEvent command) {
        getContext().getLog().info("Deserializing emergency event");
        try {
            EmergencyEventResponse emergencyEventResponse = reader.readValue(command.emergencyEventResponse());
            emergencyEvent = emergencyEventResponse.emergencyEvent();
        } catch (JsonProcessingException e) {
            getContext().getLog().error("Error parsing emergency event: {}", e.getMessage());
            return Behaviors.same();
        }
        getContext().getLog().info("Emergency event is: {}", emergencyEvent.toString());
        energyMonitorRepo.tell(new EnergyMonitorRepo.Message.SaveEmergencyStatus(emergencyEvent, apiID));
        return Behaviors.same();
    }

    private Behavior<Command> fetchAPI(FetchAPI command) {
        getContext().getLog().info("API fetched successfully");
        apiPath = command.response.api();
        apiCommand = command.response.endpoint();
        apiKey = command.response.apiKey();
        getContext().getLog().info("api: {}", apiCommand);
        return Behaviors.withTimers(timers -> {
            timers.startTimerWithFixedDelay(new FetchEmergencyEvent(getContext().getSelf()),
                    java.time.Duration.ofSeconds(0),
                    java.time.Duration.ofSeconds(command.response.delay()));
            return Behaviors.same();
        });
    }

    public static Behavior<Command> create(ObjectReader reader, ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo) {
        return Behaviors.setup(ctx -> new EmergencyResponse(ctx, reader, energyMonitorRepo));

    }

    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
                .onMessage(FetchEmergencyEvent.class, this::fetchEmergencyEvent)
                .onMessage(EmergencyRequestSuccess.class, this::parseEmergencyEvent)
                .onMessage(EmergencyRequestFailure.class, this::handleRequestFailure)
                .onMessage(EmergencyState.class, this::emergencyState)
                .onMessage(DeserializeEmergencyEvent.class, this::deserializeEmergencyEvent)
                .onMessage(FetchAPI.class, this::fetchAPI)
                .build();
    }

}
