package sa.com.demaenergy.mining.loadoptimizer.http;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.javadsl.ActorContext;
import akka.actor.typed.javadsl.Behaviors;
import akka.actor.typed.javadsl.Receive;
import sa.com.demaenergy.mining.Bitcoin.StrikePriceActor;
import sa.com.demaenergy.mining.loadoptimizer.EconomicDispatcher;
import sa.com.demaenergy.mining.loadoptimizer.EconomicDispatcher.Message.MinersPowerUsageResponse.PowerUsage;

import java.math.BigDecimal;
import java.util.List;

public class EDPowerTargetOptimizer extends AbstractBehavior<EDPowerTargetOptimizer.Message> {
    public EDPowerTargetOptimizer(ActorContext<Message> context,
                                  BigDecimal powerPrice,
                                  List<StrikePriceActor.StrikePrice> strikePrices,
                                  List<PowerUsage> powerUsages,
                                  ActorRef<EconomicDispatcher.Message> replyTo
    ) {
        super(context);
        replyTo.tell(new EconomicDispatcher.Message.OptimizedPowerTargetResponse(BigDecimal.valueOf(1000)));
    }

    public static Behavior<Message> create(BigDecimal powerPrice, List<StrikePriceActor.StrikePrice> strikePrices,
                                           List<PowerUsage> powerUsages, ActorRef<EconomicDispatcher.Message> replyTo) {
        return Behaviors.setup(context -> new EDPowerTargetOptimizer(context, powerPrice, strikePrices, powerUsages, replyTo));
    }

    @Override
    public Receive<Message> createReceive() {
        return newReceiveBuilder()
                .onMessage(Message.GetOptimizedPowerTarget.class, this::onGetOptimizedPowerTarget)
                .build();
    }

    private Behavior<Message> onGetOptimizedPowerTarget(Message.GetOptimizedPowerTarget getOptimizedPowerTarget) {
        getContext().getLog().info("Calculating optimized power target ...");

        return this;
    }

    public interface Message {
        record GetOptimizedPowerTarget(BigDecimal powerPrice,
                                       List<StrikePriceActor.StrikePrice> strikePrices,
                                       List<PowerUsage> powerUsages) implements Message {
        }

    }
}
