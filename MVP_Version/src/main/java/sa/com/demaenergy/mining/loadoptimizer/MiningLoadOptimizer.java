package sa.com.demaenergy.mining.loadoptimizer;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.javadsl.ActorContext;
import akka.actor.typed.javadsl.Behaviors;
import akka.actor.typed.javadsl.Receive;
import sa.com.demaenergy.db.EconomicDispatcherRepo;
import sa.com.demaenergy.energymonitor.DayAheadMarket;
import sa.com.demaenergy.energymonitor.EnergyMonitor;
import sa.com.demaenergy.mining.manager.MinersController;
import sa.com.demaenergy.shared.Aggregator;

import java.math.BigDecimal;
import java.time.Duration;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Consumer;

import static java.math.BigDecimal.ZERO;
import static java.time.LocalDateTime.now;

//Chain-of-responsibility_pattern???

/**
 * consider implementing: https://en.wikipedia.org/wiki/Chain-of-responsibility_pattern
 */
public class MiningLoadOptimizer extends AbstractBehavior<MiningLoadOptimizer.Message> {
    private final ActorRef<EconomicDispatcher.Message> economicDispatcher;
    private final ActorRef<MinersController.Message> minersController;
    private final ActorRef<EnergyMonitor.Command> energyMonitor;
    private final ActorRef<DayAheadMarket.Command> dayAheadMarket;
    private DispatchersResult dispatchersResult;

    public record DispatchersResult(
            BigDecimal powerTarget,
            LocalDateTime timestamp
    ) {
    }

    private MiningLoadOptimizer(ActorContext<Message> context, ActorRef<EnergyMonitor.Command> energyMonitor,
                                ActorRef<DayAheadMarket.Command> dayAheadMarket, ActorRef<MinersController.Message> minersController) {
        super(context);
        this.energyMonitor = energyMonitor;
        this.dayAheadMarket = dayAheadMarket;
        this.minersController = minersController;
        final ActorRef<EconomicDispatcherRepo.Message> economicDispatcherRepo =
                context.spawn(EconomicDispatcherRepo.create(), "EconomicDispatcherRepo");
        economicDispatcher = context.spawn(EconomicDispatcher.create(this.getContext().getSelf(), energyMonitor, economicDispatcherRepo, minersController), "EconomicDispatcher");
        getContext().getSelf().tell(new Message.GetEnergyState(this.getContext().getSelf()));
    }

    public static Behavior<Message> create(ActorRef<EnergyMonitor.Command> energyMonitor,
                                           ActorRef<DayAheadMarket.Command> dayAheadMarket,
                                           ActorRef<MinersController.Message> minersController) {
        return Behaviors.withTimers(
                timers -> {
                    timers.startTimerWithFixedDelay(new Message.LoadOptimizerTick(UUID.randomUUID()),
                            Duration.ofSeconds(0),
                            Duration.ofSeconds(200));
                    return Behaviors.setup(context -> new MiningLoadOptimizer(context, energyMonitor, dayAheadMarket,
                            minersController));
                }
        );
    }

    @Override
    public Receive<Message> createReceive() {
        return newReceiveBuilder()
                .onMessage(Message.LoadOptimizerTick.class, this::onTick)
                .onMessage(Message.PowerTarget.class, this::onPowerTarget)
                .onMessage(Message.GetEnergyState.class, this::onGetEnergyState)
                .onMessage(AggregatedEnergy.class, this::onAggregatedEnergy)
                .build();
    }

    private Behavior<Message> onPowerTarget(Message.PowerTarget powerTarget) {
        this.getContext().getLog().info("Received power target: {}", powerTarget.powerTarget);
        this.dispatchersResult = new DispatchersResult(powerTarget.powerTarget, this.dispatchersResult.timestamp);

//        TODO: call Constrained Dispatcher ...
        return Behaviors.same();
    }

    private Behavior<Message> onTick(Message.LoadOptimizerTick loadOptimizerTick) {
        this.getContext().getLog().info("Received load optimizer tick: {}", loadOptimizerTick.uuid);

        dispatchersResult = new DispatchersResult(ZERO, now());
        economicDispatcher.tell(new EconomicDispatcher.Message.GetPowerTarget(loadOptimizerTick.uuid));
        return Behaviors.same();
    }

    private Behavior<Message> onGetEnergyState(Message.GetEnergyState getEnergyState) {
        int expectedReplies = 3;
        Consumer<ActorRef<Object>> sendRequests =
                replyTo -> {
                    dayAheadMarket.tell(new DayAheadMarket.DAMPrice(replyTo.narrow()));// replace with dam
                    energyMonitor.tell(new EnergyMonitor.GetEmergencyState(replyTo.narrow()));
                    energyMonitor.tell(new EnergyMonitor.GetWattageState(replyTo.narrow()));
                };
        getContext().spawnAnonymous(
                Aggregator.create(
                        Object.class,
                        sendRequests,
                        expectedReplies,
                        getContext().getSelf(),
                        this::aggregateEnergy,
                        Duration.ofSeconds(5)));
        return Behaviors.same();
    }

    public static final class AggregatedEnergy implements Message {
        private final DayAheadMarket.DAMSubscriber damSubscriber;
        private final EnergyMonitor.EmergencySubscriber emergencySubscriber;
        private final EnergyMonitor.WattageSubscriber wattageSubscriber;

        public AggregatedEnergy(DayAheadMarket.DAMSubscriber damSubscriber, EnergyMonitor.EmergencySubscriber emergencySubscriber, EnergyMonitor.WattageSubscriber wattageSubscriber) {
            this.damSubscriber = damSubscriber;
            this.emergencySubscriber = emergencySubscriber;
            this.wattageSubscriber = wattageSubscriber;
        }
    }

    private AggregatedEnergy aggregateEnergy(List<Object> replies) {
        AtomicReference<DayAheadMarket.DAMSubscriber> marketSubscriber = new AtomicReference<>();
        AtomicReference<EnergyMonitor.EmergencySubscriber> emergencySubscriber = new AtomicReference<>();
        AtomicReference<EnergyMonitor.WattageSubscriber> wattageSubscriber = new AtomicReference<>();

        replies.forEach(reply -> {
            if (reply instanceof DayAheadMarket.DAMSubscriber damSubscriber) {
                marketSubscriber.set(damSubscriber);
            }
            if (reply instanceof EnergyMonitor.EmergencySubscriber er) {
                emergencySubscriber.set(er);
            }
            if (reply instanceof EnergyMonitor.WattageSubscriber wr) {
                wattageSubscriber.set(wr);
            }
        });
        return new AggregatedEnergy(marketSubscriber.get(), emergencySubscriber.get(), wattageSubscriber.get());
    }

    private Behavior<Message> onAggregatedEnergy(AggregatedEnergy command) {
        this.getContext().getLog().info("Received aggregated energy state DAM {}", command.damSubscriber.damPrice());
        return Behaviors.same();
    }

    public sealed interface Message {
        record LoadOptimizerTick(UUID uuid) implements Message {
        }

        record PowerTarget(BigDecimal powerTarget) implements Message {
        }

        record GetEnergyState(ActorRef<Message> ref) implements Message {
        }

    }
}
