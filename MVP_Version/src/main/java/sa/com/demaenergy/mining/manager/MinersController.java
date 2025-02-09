package sa.com.demaenergy.mining.manager;

import akka.actor.typed.*;
import akka.actor.typed.javadsl.*;
import com.typesafe.config.Config;
import org.slf4j.Logger;
import sa.com.demaenergy.db.MiningRepo;
import sa.com.demaenergy.mining.Bitcoin.StrikePriceActor;
import sa.com.demaenergy.mining.MinerActor;
import sa.com.demaenergy.mining.model.MinerSummaryRequest;

import java.math.BigDecimal;
import java.net.InetAddress;
import java.time.Duration;
import java.util.*;

import static sa.com.demaenergy.mining.MinerActor.MinerState.*;

public class MinersController extends AbstractBehavior<MinersController.Message> {
    private final ActorRef<MiningRepo.Message> miningRepo;
    final Config config = getContext().getSystem().settings().config();
    final Map<String, Miner> miners = new HashMap<>();
    final Logger log;
    final String summaryInterval = getContext().getSystem().settings().config().getString("miners.summary.fetch_interval");
    final String minersScanReceiveTimeout = getContext().getSystem().settings().config().getString("miners.scan.receive.timeout");

    public MinersController(ActorContext<Message> context, TimerScheduler<Message> timers, ActorRef<MiningRepo.Message> miningRepo) {
        super(context);
        this.miningRepo = miningRepo;
        this.log = context.getLog();
        timers.startTimerAtFixedRate("reportMinersState", new MinersReportTick(), Duration.parse(summaryInterval));
//        scanNetworkForMiners();
        miningRepo.tell(new MiningRepo.Message.GetMinersInfo(context.getSelf()));

    }

    private Behavior<Message> scanNetworkForMiners(Message.ScanNetwork scanNetwork) {

        ActorRef<PrepareMiners.Message> scanNetworkForMiners = getContext().spawn(
                Behaviors.supervise(
                        PrepareMiners.create(getContext().getSelf(), Duration.parse(minersScanReceiveTimeout))
                ).onFailure(Exception.class, SupervisorStrategy.restart()),
                "ScanNetworkForMiners",
                DispatcherSelector.blocking()
        );

        getContext().watch(scanNetworkForMiners);
        scanNetworkForMiners.tell(new PrepareMiners.Message.ScanFromSubnet(scanNetwork.subnet));
        return Behaviors.same();
    }

    public static Behavior<Message> create(ActorRef<MiningRepo.Message> miningRepo) {
        return Behaviors.withTimers(
                timers -> Behaviors.setup(
                        context -> new MinersController(context, timers, miningRepo)
                )
        );
    }

    @Override
    public Receive<Message> createReceive() {
        return newReceiveBuilder()
                .onMessage(Message.MinersIps.class, this::onMinersIps)
                .onMessage(MinersReportTick.class, this::onMinersReportTick)
                .onMessage(Message.MinerSummary.class, this::onMinerSummary)
                .onMessage(ScanFailed.class, this::onScanFailed)
                .onMessage(Message.MinerHashRate.class, this::onMinerHashRate)
                .onMessage(Message.ScanNetwork.class, this::scanNetworkForMiners)
                .onMessage(Message.MinersInfo.class, this::minersInfo)
                .onSignal(Terminated.class, this::onTerminated)
                .build();
    }

    private Behavior<Message> minersInfo(Message.MinersInfo minersInfo) {
        getContext().getLog().info("Miners Info Received from DB {}", minersInfo.minersList.size());
        getContext().getLog().debug("Miners Info Received from DB {}", minersInfo.minersList);

        minersInfo.minersList.forEach(miner -> {
            log.info("Initializing miner: {}", miner);
            ActorRef<MinerActor.Command> minerActor = getContext().spawn(
                    Behaviors.supervise(
                            MinerActor.create(miner.id(), miner.ipAddress().getHostAddress(),
                                    80, "admin", getContext().getSelf()
                            )
                    ).onFailure(Exception.class, SupervisorStrategy.restart()),
                    miner.id()
            );
//            Miner miner1 = new Miner(miner.id(), miner.ipAddress(), miner.port(), miner.desiredState());
            Miner miner1 = new Miner(miner.id(), miner.state, miner.ipAddress, miner.port,
                    miner.desiredState, 0, minerActor, null);
            miners.put(miner1.id, miner1);
            minerActor.tell(new MinerActor.Summary());
        });

        return Behaviors.same();

    }

    private Behavior<Message> onScanFailed(ScanFailed scanFailed) {
        log.error("Failed to scan network for miners");
        log.info("retrying in 5 seconds ...");
        ActorRef<PrepareMiners.Message> scanNetworkForMiners = getContext().spawn(
                Behaviors.supervise(
                        PrepareMiners.create(getContext().getSelf(), Duration.ofSeconds(10))
                ).onFailure(Exception.class, SupervisorStrategy.restart()),
                STR."ScanNetworkForMiners\{UUID.randomUUID().toString().substring(1, 10)}",
                DispatcherSelector.blocking()
        );

        getContext().watch(scanNetworkForMiners);
        scanNetworkForMiners.tell(new PrepareMiners.Message.ScanFromSubnet(config.getString("network.subnet"))); //todo: get from db
        return Behaviors.same();
    }

    private Behavior<Message> onMinersReportTick(MinersReportTick minersReportTick) {
        log.info("Reporting miners state");
        if (miners.isEmpty()) {
            log.info("No miners found");
            return Behaviors.same();
        }
        miners.forEach((_, miner) -> miner.minerActor.tell(new MinerActor.Summary()));
        return Behaviors.same();
    }

    private Behavior<Message> onMinerSummary(Message.MinerSummary minerSummary) {
        Miner miner = miners.get(minerSummary.id);

        if (miner == null) {
            log.error("Miner not found: {}", minerSummary.id);
            return Behaviors.same();
        }

        final MinerActor.MinerState minerState = valueOf(minerSummary.minerSummary.minerStatus().minerState().toUpperCase());
        int retries = 0;

        if (!Objects.equals(minerState, miner.desiredState)) {
            log.info("Miner: {} with ip: {} is not at the desired state", minerSummary.id, miner.ipAddress.getHostAddress());
            log.info("Miner: {} Retrying ... {}", minerSummary.id, miner.retries);

            retries = miner.retries + 1;

            if (retries > config.getInt("miners.retries.threshold")) {
                log.info("Miner {} with ip {} has reached the maximum number of retries", minerSummary.id, miner.ipAddress.getHostAddress());
                retries = 0;
                miner.minerActor.tell(new MinerActor.Restart(getContext().getSelf()));
            } else {
                miner.minerActor.tell(mapStateToCommand(miner.desiredState()));
            }
        } else {
            log.info("Miner: {} is in the desired state", minerSummary.id);
        }

        final Miner updatedMiner = new Miner(miner.id, minerState,
                miner.ipAddress, miner.port, miner.desiredState, retries, miner.minerActor, minerSummary.minerSummary);
        miners.put(miner.id, updatedMiner);

        miningRepo.tell(new MiningRepo.Message.SaveMinerSummary(miner, minerSummary.minerSummary, miner.desiredState, minerSummary.minerMetricsJson));
        return Behaviors.same();
    }

    private Behavior<Message> onMinerHashRate(Message.MinerHashRate minerHashRate) {
        List<StrikePriceActor.MinerHashRate> minersHashRate = new ArrayList<>();

        if (miners.values().stream().anyMatch(miner -> miner.minerSummary() == null)) {
            getContext().scheduleOnce(
                    Duration.ofSeconds(5),
                    getContext().getSelf(),
                    new Message.MinerHashRate(minerHashRate.replyTo())
            );
            return Behaviors.same();
        }

        miners.forEach((id, miner) -> minersHashRate.add(new StrikePriceActor
                .MinerHashRate(BigDecimal.valueOf(miner.minerSummary().averageHashRate()), id)));
        minerHashRate.replyTo().tell(new StrikePriceActor.Command.MinersHashRate(minersHashRate));
        return Behaviors.same();
    }

    private Behavior<Message> onTerminated(Terminated terminated) {
        log.info("Terminated: {}", terminated.getRef().path().name());
        return Behaviors.same();
    }

    private Behavior<Message> onMinersIps(Message.MinersIps minersIps) {
        log.info("Miners found: {}", minersIps.minersList.size());

        if (minersIps.minersList.isEmpty()) {
            log.info("no miners found in the network");
            return Behaviors.same();
        }
        minersIps.minersList.forEach(miner -> {
            log.info("Initializing miner: {}", miner);
            ActorRef<MinerActor.Command> minerActor = getContext().spawn(
                    Behaviors.supervise(
                            MinerActor.create(miner.id(), miner.ipAddress().getHostAddress(),
                                    80, "admin", getContext().getSelf()
                            )
                    ).onFailure(Exception.class, SupervisorStrategy.restart()),
                    miner.id()
            );
            Miner miner1 = new Miner(miner.id(), miner.state, miner.ipAddress, miner.port,
                    MINING, 0, minerActor, null);

            miners.put(miner1.id, miner1);
            miningRepo.tell(new MiningRepo.Message.SaveMinerInitialization(miner1, miner1.desiredState.name()));
            minerActor.tell(new MinerActor.Summary());
        });

        return Behaviors.same();
    }

    private MinerActor.Command mapStateToCommand(MinerActor.MinerState state) {
        return switch (state) {
            case INITIALIZING, STARTING -> new MinerActor.Start(getContext().getSelf());
            case RESTARTING -> new MinerActor.Restart(getContext().getSelf());
            case STOPPED -> new MinerActor.Pause(getContext().getSelf());
            case MINING -> new MinerActor.Resume(getContext().getSelf());
            case FAILURE -> new MinerActor.Stop(getContext().getSelf());
        };
    }

    public record Miner(String id, MinerActor.MinerState state, InetAddress ipAddress, int port,
                        MinerActor.MinerState desiredState,
                        int retries, ActorRef<MinerActor.Command> minerActor,
                        MinerSummaryRequest.MinerSummary minerSummary) {
        Miner(String id, InetAddress ipAddress, int port) {
            this(id, INITIALIZING, ipAddress, port, MINING, 0, null, null);
        }

        public Miner(String id, InetAddress ipAddress, int port, MinerActor.MinerState desiredState) {
            this(id, INITIALIZING, ipAddress, port, desiredState, 0, null, null);
        }

        @Override
        public boolean equals(Object obj) {
            if (this == obj) return true;
            if (obj == null || getClass() != obj.getClass()) return false;
            Miner miner = (Miner) obj;
            return id.equals(miner.id);
        }
    }

    public interface Message {

        record MinersIps(List<Miner> minersList) implements Message {
        }

        record MinerSummary(String id, MinerSummaryRequest.MinerSummary minerSummary,
                            String minerMetricsJson) implements Message {
        }

        record MinerHashRate(ActorRef<StrikePriceActor.Command> replyTo) implements Message {
        }

        record ScanNetwork(String subnet) implements Message {
        }

        public record MinersInfo(List<Miner> minersList) implements Message {
        }
    }

    private record MinersReportTick() implements Message {
    }

    public record ScanFailed() implements Message {
    }


}
