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
import sa.com.demaenergy.energymonitor.model.EnergyPriceResponse;
import sa.com.demaenergy.energymonitor.model.EnergyPriceResponse.EnergyPrice;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.CompletionStage;

import static java.time.Duration.ofSeconds;

public class RealTimeMarket extends AbstractBehavior<RealTimeMarket.Command> {
    private final ObjectReader reader;
    private final ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo;
    private final Http http = Http.get(getContext().getSystem());
    private String apiKey;
    private String apiPath;
    private String apiCommand;
    int apiID = getContext().getSystem().settings().config().getInt("lmp.api-id"); //todo: should fetch from db
    private final String lmpProductID = getContext().getSystem().settings().config().getString("lmp.product-id");
    private EnergyPrice energyPrice;

    public sealed interface Command {
    }

    public record MarketState(ActorRef<EnergyMonitor.Command> replyTo, UUID requestID) implements Command {
    }

    private record PriceRequestSuccess(HttpResponse httpResponse) implements Command {
    }

    private record DeserializeEnergyPrice(String energyPrice) implements Command {
    }

    private record PriceRequestFailure(Throwable th) implements Command {
    }

    private record FetchEnergyPrice(ActorRef<Command> replyTo) implements Command {
    }

    private record FetchAPI(EnergyMonitorRepo.Message.Response.APIResponse response) implements Command {
    }

    private RealTimeMarket(ActorContext<Command> context,
                           ObjectReader reader, ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo) {
        super(context);
        this.reader = reader;
        this.energyMonitorRepo = energyMonitorRepo;
        ActorRef<EnergyMonitorRepo.Message.Response.APIResponse> apiResponseActor = context.messageAdapter(EnergyMonitorRepo.Message.Response.APIResponse.class,
                FetchAPI::new
        );
        this.energyMonitorRepo.tell(new EnergyMonitorRepo.Message.GetAPI(apiResponseActor, apiID));
        getContext().getLog().info("Fetching Energy Price API");

    }

    private Behavior<Command> fetchEnergyPrice(FetchEnergyPrice command) {
        getContext().getLog().info("Fetching energy price");
        List<HttpHeader> headers = List.of(Authorization.
                parse("Authorization", String.format("Basic %s", apiKey)));
        String payLoad = "command=%s&a={\"productID\":\"%s\"}".formatted(apiCommand, lmpProductID);

        CompletionStage<HttpResponse> request = http.singleRequest(HttpRequest
                .POST(apiPath).withHeaders(headers)
                .withEntity(HttpEntities.create(ContentTypes.APPLICATION_X_WWW_FORM_URLENCODED, payLoad)));

        getContext().pipeToSelf(request, (httpResponse, th) -> {
            if (th != null) {
                return new PriceRequestFailure(th);
            } else {
                return new PriceRequestSuccess(httpResponse);
            }
        });
        return Behaviors.same();
    }

    private Behavior<Command> parseEnergyPrice(PriceRequestSuccess command) {
        getContext().getLog().info("Energy price fetched successfully");

        List<String> tempEnergyPrice = new ArrayList<>();
        command.httpResponse.entity().getDataBytes()
                .map(ByteString::utf8String)
                .runForeach(tempEnergyPrice::add, getContext().getSystem())
                .thenAccept(done -> getContext().getSelf().tell(new DeserializeEnergyPrice(tempEnergyPrice.getFirst())));

        return Behaviors.same();
    }

    private Behavior<Command> handleRequestFailure(PriceRequestFailure command) {
        getContext().getLog().error("Error fetching energy price: {}", command.th.getMessage());
        return Behaviors.same();
    }

    private Behavior<Command> marketState(MarketState command) {
        if (energyPrice == null) {
            getContext().scheduleOnce(ofSeconds(1),
                    getContext().getSelf(),
                    command);
            return Behaviors.same();
        }

        command.replyTo.tell(new EnergyMonitor.MarketStateResponse(energyPrice, command.requestID));
        return Behaviors.same();
    }

    private Behavior<Command> deserializeEnergyPrice(DeserializeEnergyPrice command) {
        getContext().getLog().info("Deserializing energy price");
        try {
            EnergyPriceResponse energyPriceResponse = reader.readValue(command.energyPrice());
            energyPrice = energyPriceResponse.energyPrice().getFirst();
            energyMonitorRepo.tell(new EnergyMonitorRepo.Message.SaveRTMPrice(energyPrice.price(), apiID));
        } catch (JsonProcessingException e) {
            getContext().getLog().error("Error parsing energy price: {}", e.getMessage());
            return Behaviors.same();
        }
        getContext().getLog().info("Energy price is: {}", energyPrice.toString());
        return Behaviors.same();
    }

    private Behavior<Command> fetchAPI(FetchAPI command) {
        getContext().getLog().info("API fetched successfully");
        apiPath = command.response.api();
        apiCommand = command.response.endpoint();
        apiKey = command.response.apiKey();
        getContext().getLog().info("api: {}", apiCommand);
        return Behaviors.withTimers(timers -> {
            timers.startTimerWithFixedDelay(new FetchEnergyPrice(getContext().getSelf()),
                    ofSeconds(0),
                    ofSeconds(command.response.delay()));
            return Behaviors.same();
        });
    }

    public static Behavior<Command> create(ObjectReader objectReader, ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo) {
        return Behaviors.setup(ctx -> new RealTimeMarket(ctx, objectReader, energyMonitorRepo));
    }

    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
                .onMessage(FetchEnergyPrice.class, this::fetchEnergyPrice)
                .onMessage(PriceRequestSuccess.class, this::parseEnergyPrice)
                .onMessage(PriceRequestFailure.class, this::handleRequestFailure)
                .onMessage(MarketState.class, this::marketState)
                .onMessage(DeserializeEnergyPrice.class, this::deserializeEnergyPrice)
                .onMessage(FetchAPI.class, this::fetchAPI)
                .build();
    }
}
