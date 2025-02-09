package sa.com.demaenergy.mining.Bitcoin;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.javadsl.ActorContext;
import akka.actor.typed.javadsl.Behaviors;
import akka.actor.typed.javadsl.Receive;
import sa.com.demaenergy.db.StrikePriceRepo;
import sa.com.demaenergy.db.StrikePriceRepo.Message.SaveStrikePrice;
import sa.com.demaenergy.mining.loadoptimizer.EconomicDispatcher;
import sa.com.demaenergy.mining.manager.MinersController;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;

import static java.math.BigDecimal.valueOf;

public class StrikePriceActor extends AbstractBehavior<StrikePriceActor.Command> {
    private final ActorRef<EconomicDispatcher.Message> replyTo;
    private final ActorRef<StrikePriceRepo.Message> strikePriceRepo;
    private final ActorRef<MinersController.Message> minersController;
    private double hashprice;
    private List<MinerHashRate> minersHashRate;
    private final int expectedResponseCount = 3;
    private int responseCount = 0;
    private double c1, c2, c3;

    public StrikePriceActor(ActorContext<Command> context,
                            ActorRef<EconomicDispatcher.Message> replyTo,
                            ActorRef<StrikePriceRepo.Message> strikePriceRepo, ActorRef<MinersController.Message> minersController) {
        super(context);
        this.replyTo = replyTo;
        this.strikePriceRepo = strikePriceRepo;
        this.minersController = minersController;
        getDependenciesForStrikePriceCalculation(context, strikePriceRepo);

    }

    private void getDependenciesForStrikePriceCalculation(ActorContext<Command> context, ActorRef<StrikePriceRepo.Message> strikePriceRepo) {
        ActorRef<HashPrice.Command> hashPriceActor = getContext().spawn(HashPrice.create(getContext().getSelf()), "HashPrice");
        hashPriceActor.tell(new HashPrice.GetHashPriceRequest());
        minersController.tell(new MinersController.Message.MinerHashRate(context.getSelf()));
//        context.getSelf().tell(new Command.MinersHashRate(generateDummyMinersHashRates()));
        strikePriceRepo.tell(new StrikePriceRepo.Message.GetConstants(context.getSelf()));
    }

//    todo zbtha
    private static List<MinerHashRate> generateDummyMinersHashRates() {
        return List.of(
                new MinerHashRate(new BigDecimal("132412341234"), "1"),
                new MinerHashRate(new BigDecimal("132412341234"), "1"),
                new MinerHashRate(new BigDecimal("132412341234"), "1"),
                new MinerHashRate(new BigDecimal("132412341234"), "1")
        );
    }

    public static Behavior<Command> create(ActorRef<EconomicDispatcher.Message> replyTo,
                                           ActorRef<StrikePriceRepo.Message> strikePriceRepo,
                                           ActorRef<MinersController.Message> minersController) {
        return Behaviors.setup(context -> new StrikePriceActor(context, replyTo, strikePriceRepo, minersController));
    }


    private Behavior<Command> onMinersHashRate(Command.MinersHashRate minersHashRate) {
        this.minersHashRate = minersHashRate.minersHashRate;

        return checkResponses();
    }

    private Behavior<Command> checkResponses() {
        responseCount++;
        if (responseCount == expectedResponseCount) {
            List<StrikePrice> strikePrices = new ArrayList<>();
            for (MinerHashRate minersHashRate : minersHashRate) {
//                TODO: Ideally, we should get the equation as a string and run it rather than writing code to calculate it
                final BigDecimal minerPowerConsumptionConsideringHashRate = minersHashRate.hashRate
                        .pow(2)
                        .multiply(valueOf(c1))
                        .add(minersHashRate.hashRate.multiply(valueOf(c2)))
                        .add(valueOf(c3));

                final BigDecimal minerEfficiency = minerPowerConsumptionConsideringHashRate.divide(minersHashRate.hashRate, 10, RoundingMode.HALF_UP);
                final BigDecimal minerStrikePrice = minerEfficiency.multiply(valueOf(hashprice));

                StrikePrice strikePrice1 = new StrikePrice(minersHashRate.hashRate, minerStrikePrice, minerEfficiency, hashprice,
                        minersHashRate.minerId
                );
                strikePriceRepo.tell(new SaveStrikePrice(
                                strikePrice1.minersHashRate,
                                strikePrice1.strikePrice,
                                strikePrice1.minerEfficiency,
                                strikePrice1.hashprice,
                                strikePrice1.minerId
                        )
                );
                strikePrices.add(strikePrice1);
            }

            replyTo.tell(new EconomicDispatcher.Message.StrikePriceResponse(strikePrices));
            return Behaviors.stopped();
        }

        return Behaviors.same();
    }

    private Behavior<Command> onGetHashPriceResponse(Command.GetHashPriceResponse getHashPriceResponse) {
        this.hashprice = getHashPriceResponse.hashPriceUSD;
        return checkResponses();
    }

    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
                .onMessage(Command.GetHashPriceResponse.class, this::onGetHashPriceResponse)
                .onMessage(Command.MinersHashRate.class, this::onMinersHashRate)
                .onMessage(Command.GetConstantsResponse.class, this::onGetConstants)
                .build();
    }

    private Behavior<Command> onGetConstants(Command.GetConstantsResponse getConstantsResponse) {
        this.c1 = getConstantsResponse.c1;
        this.c2 = getConstantsResponse.c2;
        this.c3 = getConstantsResponse.c3;
        return this.checkResponses();
    }


    public sealed interface Command {
        record GetHashPriceResponse(double hashPriceUSD) implements Command {
        }

        record GetConstantsResponse(double c1, double c2, double c3) implements Command {
        }

        record MinersHashRate(List<MinerHashRate> minersHashRate) implements Command {
        }
    }

    public record MinerHashRate(BigDecimal hashRate, String minerId) {
    }

    public record StrikePrice(BigDecimal minersHashRate, BigDecimal strikePrice, BigDecimal minerEfficiency,
                              double hashprice, String minerId) {
    }
}
