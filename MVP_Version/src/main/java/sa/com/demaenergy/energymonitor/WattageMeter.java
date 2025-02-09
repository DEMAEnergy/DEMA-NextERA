package sa.com.demaenergy.energymonitor;


import sa.com.demaenergy.db.EnergyMonitorRepo;
import sa.com.demaenergy.energymonitor.model.PLCReading;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.*;

import org.apache.plc4x.java.api.PlcConnection;
import org.apache.plc4x.java.api.PlcDriverManager;
import org.apache.plc4x.java.api.exceptions.PlcConnectionException;
import org.apache.plc4x.java.api.messages.PlcReadRequest;
import org.apache.plc4x.java.api.messages.PlcReadResponse;
import org.apache.plc4x.java.api.types.PlcResponseCode;

import java.util.UUID;
import java.util.concurrent.ExecutionException;

public class WattageMeter extends AbstractBehavior<WattageMeter.Command> {
    private final ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo;
    private final int plcID;
    private int plcRegister;
    private String connectionString;
    private PLCReading plcReading;

    public WattageMeter(ActorContext<Command> context, int plcID,
                        ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo) {
        super(context);
        this.plcID = plcID;
        this.energyMonitorRepo = energyMonitorRepo;
        ActorRef<EnergyMonitorRepo.Message.Response.PLCResponse> plcResponseActor = context.messageAdapter(EnergyMonitorRepo.Message.Response.PLCResponse.class,
                FetchPLC::new
        );
        this.energyMonitorRepo.tell(new EnergyMonitorRepo.Message.GetPLC(plcResponseActor, plcID));
    }

    public sealed interface Command {
    }

    public record WattageState(ActorRef<EnergyMonitor.Command> replyTo, UUID requestID) implements Command {
    }

    private record FetchWattage() implements Command {
    }
    private record FetchPLC(EnergyMonitorRepo.Message.Response.PLCResponse response) implements Command {}


    private Behavior<Command> fetchWattageMeter(FetchWattage command) {
        getContext().getLog().info("Fetching wattage meter");

        try (PlcConnection plcConnection = PlcDriverManager.getDefault().getConnectionManager().getConnection(connectionString)) {
            PlcReadRequest.Builder builder = plcConnection.readRequestBuilder();

            PlcReadRequest request = builder.addTagAddress("wattage",
                    "holding-register:%s".formatted(plcRegister)).build();
            PlcReadResponse response = request.execute().get(5, java.util.concurrent.TimeUnit.SECONDS);
            if (response.getResponseCode("wattage") == PlcResponseCode.OK) {
                plcReading = new PLCReading(response.getInteger("wattage"));
                getContext().getLog().info("Wattage: {}", plcReading.wattage());
                energyMonitorRepo.tell(new EnergyMonitorRepo.Message.SaveWattageReading(plcReading, plcID));
            } else {
                getContext().getLog().error("Error fetching wattage meter status: {}",
                        response.getResponseCode("wattage").name());
            }
        } catch (ExecutionException | InterruptedException | PlcConnectionException e) {
            getContext().getLog().error("Error fetching wattage meter", e);
        } catch (Exception e) {
            getContext().getLog().error("Undefined error while fetching wattage meter", e);
        }
        return Behaviors.same();
    }

    private Behavior<Command> fetchPLC(FetchPLC command) {
        this.plcRegister = command.response.plcRegister();
        this.connectionString = "modbus-tcp://%s:%d".formatted(command.response.plcIP(),
                command.response.plcPort());

        return Behaviors.withTimers(timers -> {
            timers.startTimerWithFixedDelay(new FetchWattage(),
                    java.time.Duration.ofSeconds(0),
                    java.time.Duration.ofSeconds(300));
            return Behaviors.same();
        });
    }

    private Behavior<Command> wattageState(WattageState command) {
        command.replyTo.tell(new EnergyMonitor.WattageStateResponse(plcReading, command.requestID));
        return Behaviors.same();
    }

    public static Behavior<Command> create(int plcID, ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo) {
        return Behaviors.setup(ctx -> new WattageMeter(ctx, plcID, energyMonitorRepo));
    }

    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
                .onMessage(WattageState.class, this::wattageState)
                .onMessage(FetchWattage.class, this::fetchWattageMeter)
                .onMessage(FetchPLC.class, this::fetchPLC)
                .build();
    }
}
