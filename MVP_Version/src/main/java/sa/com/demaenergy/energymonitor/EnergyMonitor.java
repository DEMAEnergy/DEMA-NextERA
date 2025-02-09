package sa.com.demaenergy.energymonitor;


import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.SupervisorStrategy;
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.javadsl.ActorContext;
import akka.actor.typed.javadsl.Behaviors;
import akka.actor.typed.javadsl.Receive;
import com.fasterxml.jackson.databind.ObjectMapper;
import sa.com.demaenergy.db.EnergyMonitorRepo;
import sa.com.demaenergy.energymonitor.model.EmergencyEventResponse;
import sa.com.demaenergy.energymonitor.model.EmergencyEventResponse.EmergencyEvent;
import sa.com.demaenergy.energymonitor.model.EnergyPriceResponse;
import sa.com.demaenergy.energymonitor.model.EnergyPriceResponse.EnergyPrice;
import sa.com.demaenergy.energymonitor.model.PLCReading;
import sa.com.demaenergy.energymonitor.model.PredictedPrices;

import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

public class EnergyMonitor extends AbstractBehavior<EnergyMonitor.Command> {

    private final ActorRef<EmergencyResponse.Command> emergencyResponse;
    private final ActorRef<RealTimeMarket.Command> realTimeMarket;
    private final ActorRef<WattageMeter.Command> wattageMeter;
//    private final ActorRef<MarketPrediction.Command> marketPrediction;
    private final Map<UUID, ActorRef<MarketSubscriber>> marketRequests = new ConcurrentHashMap<>();
    private final Map<UUID, ActorRef<EmergencySubscriber>> emergencyRequests = new ConcurrentHashMap<>();
    private final Map<UUID, ActorRef<WattageSubscriber>> wattageRequests = new ConcurrentHashMap<>();

    public sealed interface Command {
    }

    // requests from subscribers
    public record GetMarketStatePrice(ActorRef<MarketSubscriber> replyTo) implements Command {}
    public record GetEmergencyState(ActorRef<EmergencySubscriber> replyTo) implements Command {}
    public record GetWattageState(ActorRef<WattageSubscriber> replyTo) implements Command {}

    // responses to subscribers
    public sealed interface Subscriber extends Command {}
    public record MarketSubscriber(EnergyPrice energyPrice) implements Subscriber {}
    public record EmergencySubscriber(EmergencyEvent emergencyEvent) implements Subscriber {}
    public record WattageSubscriber(PLCReading plcReading) implements Subscriber {}

    // responses from children
    public record MarketStateResponse(EnergyPrice energyPrice, UUID requestID) implements Command {}
    public record EmergencyStateResponse(EmergencyEvent emergencyEventResponse, UUID requestID) implements Command {}
    public record WattageStateResponse(PLCReading plcReading, UUID requestID) implements Command {}
    public record MarketPredictionResponse(List<PredictedPrices> predictedPrices, UUID requestID) implements Command {}

    // Constructor
    public EnergyMonitor(ActorContext<Command> context, ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo) {
        super(context);
        ObjectMapper objectMapper = new ObjectMapper();

        emergencyResponse = context.spawn(Behaviors.supervise(EmergencyResponse.create(objectMapper.readerFor(EmergencyEventResponse.class), energyMonitorRepo))
                .onFailure(SupervisorStrategy.restart()), "EmergencyDude");
        realTimeMarket = context.spawn(Behaviors.supervise(RealTimeMarket
                        .create(objectMapper.readerFor(EnergyPriceResponse.class), energyMonitorRepo))
                .onFailure(SupervisorStrategy.restart()), "MarketDude");
        final int plcId = getContext().getSystem().settings().config().getInt("plc.id"); //Todo: get from db
        wattageMeter = context.spawn(Behaviors.supervise(WattageMeter
                        .create(plcId, energyMonitorRepo))
                .onFailure(SupervisorStrategy.restart()), "WattageDude");
//        marketPrediction = context.spawn(Behaviors.supervise(MarketPrediction.create(energyMonitorRepo))
//                .onFailure(SupervisorStrategy.restart()), "MarketPrediction");
    }


    private Behavior<Command> onMarketStateResponse(MarketStateResponse command) {
        getContext().getLog().info("Market state response received");
        marketRequests.get(command.requestID()).tell(new MarketSubscriber(command.energyPrice()));
        marketRequests.remove(command.requestID());
        return Behaviors.same();
    }

    private Behavior<Command> onWattageResponse(WattageStateResponse command) {
        wattageRequests.get(command.requestID()).tell(new WattageSubscriber(command.plcReading()));
        wattageRequests.remove(command.requestID());
        return Behaviors.same();
    }

    private Behavior<Command> onEmergencyStateResponse(EmergencyStateResponse command) {
        emergencyRequests.get(command.requestID()).tell(new EmergencySubscriber(command.emergencyEventResponse()));
        emergencyRequests.remove(command.requestID());
        return Behaviors.same();
    }

    private Behavior<Command> onGetMarketStatePrice(GetMarketStatePrice getMarketStatePrice) {
        getContext().getLog().info("Received request for market state price");
        UUID requestId = UUID.randomUUID();
        marketRequests.put(requestId, getMarketStatePrice.replyTo());
        realTimeMarket.tell(new RealTimeMarket.MarketState(getContext().getSelf(), requestId));
        return Behaviors.same();
    }

    private Behavior<Command> onGetEmergencyState(GetEmergencyState getEmergencyState) {
        UUID requestId = UUID.randomUUID();
        emergencyRequests.put(requestId, getEmergencyState.replyTo());
        emergencyResponse.tell(new EmergencyResponse.EmergencyState(getContext().getSelf(), requestId));
        return Behaviors.same();
    }

    private Behavior<Command> onGetWattageState(GetWattageState getWattageState) {
        UUID requestId = UUID.randomUUID();
        wattageRequests.put(requestId, getWattageState.replyTo());
        wattageMeter.tell(new WattageMeter.WattageState(getContext().getSelf(), requestId));
        return Behaviors.same();
    }

    public static Behavior<Command> create(ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo) {
        return Behaviors.setup(
                context -> new EnergyMonitor(context, energyMonitorRepo));
    }

    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
                .onMessage(GetMarketStatePrice.class, this::onGetMarketStatePrice)
                .onMessage(GetEmergencyState.class, this::onGetEmergencyState)
                .onMessage(GetWattageState.class, this::onGetWattageState)
                .onMessage(MarketStateResponse.class, this::onMarketStateResponse)
                .onMessage(EmergencyStateResponse.class, this::onEmergencyStateResponse)
                .onMessage(WattageStateResponse.class, this::onWattageResponse)
                .build();
    }
}