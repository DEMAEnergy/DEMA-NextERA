package sa.com.demaenergy.examples;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.javadsl.ActorContext;
import akka.actor.typed.javadsl.Behaviors;
import akka.actor.typed.javadsl.Receive;
import sa.com.demaenergy.db.EnergyMonitorRepo;

import java.math.BigDecimal;

public class RepoClient extends AbstractBehavior<RepoClient.Command> {

    final ActorRef<EnergyMonitorRepo.Message.Response.RTMPriceResponse> rtmPriceResponseActorRef;

    public sealed interface Command {
        record GetRTMPrice(EnergyMonitorRepo.Message.Response.RTMPriceResponse response) implements Command {
        }
    }

    public static Behavior<Command> create() {
        return Behaviors.setup(
                RepoClient::new
        );
    }

    private RepoClient(ActorContext<Command> context) {
        super(context);
        rtmPriceResponseActorRef = context.messageAdapter(EnergyMonitorRepo.Message.Response.RTMPriceResponse.class,
                RepoClient.Command.GetRTMPrice::new
        );
        ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo = context.spawn(EnergyMonitorRepo.create(), "EnergyMonitorRepo");
//        for (int i = 0; i < 10; i++) {
//            String randomPrice = String.valueOf(Math.random() * 100);
//            energyMonitorRepo.tell(
//                    new EnergyMonitorRepo.Message.SaveRTMPrice(
//                            new BigDecimal(randomPrice, 1)
//                    )
//            );
//        }

        energyMonitorRepo.tell(new EnergyMonitorRepo.Message.GetRTMPrice(rtmPriceResponseActorRef));
    }

    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
                .onMessage(Command.GetRTMPrice.class, this::onGetRTMPrice)
                .build();
    }

    private Behavior<Command> onGetRTMPrice(Command.GetRTMPrice getRTMPrice) {
        getContext().getLog().info("Received RTM price: {}", getRTMPrice.response().price());
        return Behaviors.same();
    }

}
