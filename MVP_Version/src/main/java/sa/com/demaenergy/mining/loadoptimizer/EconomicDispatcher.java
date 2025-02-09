package sa.com.demaenergy.mining.loadoptimizer;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.javadsl.ActorContext;
import akka.actor.typed.javadsl.Behaviors;
import akka.actor.typed.javadsl.Receive;
import sa.com.demaenergy.db.EconomicDispatcherRepo;
import sa.com.demaenergy.db.StrikePriceRepo;
import sa.com.demaenergy.energymonitor.EnergyMonitor;
import sa.com.demaenergy.mining.Bitcoin.StrikePriceActor;
import sa.com.demaenergy.mining.loadoptimizer.MiningLoadOptimizer.Message.PowerTarget;
import sa.com.demaenergy.mining.manager.MinersController;
import sa.com.demaenergy.mining.loadoptimizer.http.EDPowerTargetOptimizer;

import java.math.BigDecimal;
import java.util.List;
import java.util.Objects;
import java.util.UUID;

import static sa.com.demaenergy.mining.loadoptimizer.EconomicDispatcher.Message.*;

public class EconomicDispatcher extends AbstractBehavior<EconomicDispatcher.Message> {
    private final ActorRef<MiningLoadOptimizer.Message> miningLoadOptimizer;
    private final ActorRef<EnergyMonitor.Command> energyMonitor;
    private final ActorRef<EnergyMonitor.MarketSubscriber> marketSubscriberActorRef;
    private final ActorRef<MinersController.Message> minersController;
    private final ActorRef<EconomicDispatcherRepo.Message> economicDispatcherRepo;
    private BigDecimal powerPrice;
    private final ActorRef<StrikePriceRepo.Message> strikePriceRepo;
    private List<StrikePriceActor.StrikePrice> strikePrices;
    private List<MinersPowerUsageResponse.PowerUsage> minersPowerUsages;

    private EconomicDispatcher(ActorContext<Message> context,
                               ActorRef<MiningLoadOptimizer.Message> miningLoadOptimizer,
                               ActorRef<EnergyMonitor.Command> energyMonitor,
                               ActorRef<EconomicDispatcherRepo.Message> economicDispatcherRepo,
                               ActorRef<MinersController.Message> minersController) {
        super(context);

        marketSubscriberActorRef = context.messageAdapter(
                EnergyMonitor.MarketSubscriber.class,
                marketSubscriber -> new PowerPriceResponse(marketSubscriber.energyPrice().price())
        );
        this.minersController = minersController;
        strikePriceRepo = getContext().spawn(StrikePriceRepo.create(), "StrikePriceRepo");
        this.energyMonitor = energyMonitor;
        this.miningLoadOptimizer = miningLoadOptimizer;
        this.economicDispatcherRepo = economicDispatcherRepo;
    }

    public static Behavior<Message> create(ActorRef<MiningLoadOptimizer.Message> miningLoadOptimizer,
                                           ActorRef<EnergyMonitor.Command> energyMonitor,
                                           ActorRef<EconomicDispatcherRepo.Message> economicDispatcherRepo,
                                           ActorRef<MinersController.Message> minersController) {
        return Behaviors.setup(context ->
                new EconomicDispatcher(context, miningLoadOptimizer, energyMonitor, economicDispatcherRepo,
                        minersController)
        );
    }

    @Override
    public Receive<Message> createReceive() {
        return initialState();
    }


    private Behavior<Message> onMinersPowerUsageResponse(MinersPowerUsageResponse minersPowerUsageResponse) {
        getContext().getLog().info("Received miners power usage: {}", minersPowerUsageResponse);
        this.minersPowerUsages = minersPowerUsageResponse.powerUsages;
        getContext().spawn(EDPowerTargetOptimizer.create(this.powerPrice,
                this.strikePrices,
                minersPowerUsageResponse.powerUsages,
                getContext().getSelf()
        ), "EDPowerTargetOptimizer");
        return Behaviors.same();
    }

    private Behavior<Message> onStrikePriceResponse(StrikePriceResponse strikePriceResponse) {
        this.strikePrices = strikePriceResponse.strikePrices;
        getContext().getLog().info("Received strike price response: {}", strikePriceResponse.strikePrices);
//        TODO
        List<MinersPowerUsageResponse.PowerUsage> powerUsages = List.of(
                new MinersPowerUsageResponse.PowerUsage(new BigDecimal("1000"), "miner1"),
                new MinersPowerUsageResponse.PowerUsage(new BigDecimal("2000"), "miner2")
        );

        getContext().getSelf().tell(new MinersPowerUsageResponse(powerUsages));
        return Behaviors.same();
    }

    private Behavior<Message> onOptimizedPowerTargetResponse(OptimizedPowerTargetResponse optimizedPowerTargetResponse) {
        getContext().getLog().info("Received optimized power target: {}", optimizedPowerTargetResponse.optimizedPowerTarget);
        economicDispatcherRepo.tell(
                new EconomicDispatcherRepo.Message.SaveEconomicDispatcherMetadata(this.powerPrice,
                        this.strikePrices, this.minersPowerUsages,
                        optimizedPowerTargetResponse.optimizedPowerTarget)
        );
//        todo call python
//
        miningLoadOptimizer.tell(new PowerTarget(optimizedPowerTargetResponse.optimizedPowerTarget));

        return initialState();
    }


    private Behavior<Message> onPowerPriceResponse(PowerPriceResponse powerPriceResponse) {
        getContext().getLog().info("Received power price: {}", powerPriceResponse.powerPrice);
        if (!Objects.equals(powerPriceResponse.powerPrice, this.powerPrice)) {
            this.powerPrice = powerPriceResponse.powerPrice;
            getContext().spawn(StrikePriceActor.create(getContext().getSelf(), this.strikePriceRepo,
                            minersController),
                    STR."StrikePrice\{UUID.randomUUID()}");
        } else {
            getContext().getLog().info("RTM has not changed");
            getContext().getLog().info("Not continuing with the strike price request.");
            return initialState();
        }

        return Behaviors.same();
    }

    private Behavior<Message> onGetPowerTarget(GetPowerTarget getPowerTarget) {
        getContext().getLog().info("Received GetPowerTarget request with uuid: {}", getPowerTarget.uuid);
        energyMonitor.tell(new EnergyMonitor.GetMarketStatePrice(marketSubscriberActorRef));
        return activeState();
    }

    private Receive<Message> initialState() {
        return newReceiveBuilder()
                .onMessage(GetPowerTarget.class, this::onGetPowerTarget)
                .build();
    }

    private Behavior<Message> activeState() {
        return newReceiveBuilder()
                .onMessage(PowerPriceResponse.class, this::onPowerPriceResponse)
                .onMessage(StrikePriceResponse.class, this::onStrikePriceResponse)
                .onMessage(MinersPowerUsageResponse.class, this::onMinersPowerUsageResponse)
                .onMessage(OptimizedPowerTargetResponse.class, this::onOptimizedPowerTargetResponse)
                .onAnyMessage(
                        message -> {
                            getContext().getLog().info("Received a message {} while in active state. Ignoring it.", message);
                            return Behaviors.same();
                        }
                )
                .build();
    }

    public interface Message {
        record GetPowerTarget(UUID uuid) implements Message {
        }

        record MinersPowerUsageResponse(List<PowerUsage> powerUsages) implements Message {
            public record PowerUsage(BigDecimal powerUsage, String minerId) {
            }

        }

        record PowerPriceResponse(BigDecimal powerPrice) implements Message {
        }

        record OptimizedPowerTargetResponse(BigDecimal optimizedPowerTarget) implements Message {
        }

        record StrikePriceResponse(List<StrikePriceActor.StrikePrice> strikePrices) implements Message {
        }
    }
}
