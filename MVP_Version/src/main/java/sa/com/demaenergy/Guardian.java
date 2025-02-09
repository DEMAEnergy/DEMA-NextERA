package sa.com.demaenergy;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.javadsl.ActorContext;
import akka.actor.typed.javadsl.Behaviors;
import akka.actor.typed.javadsl.Receive;
import sa.com.demaenergy.db.EnergyMonitorRepo;
import sa.com.demaenergy.db.MiningRepo;
import sa.com.demaenergy.energymonitor.DayAheadMarket;
import sa.com.demaenergy.energymonitor.EnergyMonitor;
import sa.com.demaenergy.mining.loadoptimizer.MiningLoadOptimizer;
import sa.com.demaenergy.mining.manager.MinersController;

public class Guardian extends AbstractBehavior<Guardian.Command> {

    public interface Command {
    }

    public static Behavior<Command> create() {
        return Behaviors.setup(
                Guardian::new
        );
    }

    private Guardian(ActorContext<Command> context) {
        super(context);

//        todo: check location table and create an actor for each site, give location id to SiteActor

        ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo = context.spawn(EnergyMonitorRepo.create(),
                "EnergyMonitorRepo");
        ActorRef<EnergyMonitor.Command> energyMonitor = context.spawn(EnergyMonitor.create(energyMonitorRepo), "EnergyMonitor");
        ActorRef<DayAheadMarket.Command> dayAheadMarket = context.spawn(DayAheadMarket.create(energyMonitorRepo), "DayAheadMarket");
        ActorRef<MiningRepo.Message> miningRepo = context.spawn(MiningRepo.create(), "MiningRepo");
        ActorRef<MinersController.Message> minersController = context.spawn(MinersController.create(miningRepo), "MinersController");
        ActorRef<MiningLoadOptimizer.Message> miningLoadOptimizer = context.spawn(MiningLoadOptimizer.create(energyMonitor, dayAheadMarket, minersController), "MiningLoadOptimizer");


        //todo:try this plz @salman
//        ActorRef<FacadeActor.Command> FA = context.spawn(FacadeActor.create(),"FA");
//        FA.tell(new FacadeActor.GetMachineSelectionOpt(getContext().getSelf(),1000, // Target Power
//                new ArrayList<>(Arrays.asList(0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2)), // Phase Assignments
//                new ArrayList<>(Arrays.asList(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)), // Previous State
//                0.36F, // Energy Price
//                29.72F, // Hash Price
//                Arrays.asList(65.0, 70.0, 75.0, 65.0, 70.0, 75.0, 65.0, 70.0, 75.0, 65.0, 70.0, 75.0)) // Hashrate Per Machine
//        );

    }

    @Override
    public Receive<Command> createReceive() {
        return null;
    }

}
