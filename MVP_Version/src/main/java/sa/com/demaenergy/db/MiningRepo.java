package sa.com.demaenergy.db;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.javadsl.ActorContext;
import akka.actor.typed.javadsl.Behaviors;
import akka.actor.typed.javadsl.Receive;
import org.postgresql.util.PGobject;
import sa.com.demaenergy.mining.MinerActor;
import sa.com.demaenergy.mining.MinerActor.MinerState;
import sa.com.demaenergy.mining.manager.MinersController;
import sa.com.demaenergy.mining.model.MinerSummaryRequest;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.sql.*;
import java.util.ArrayList;
import java.util.List;

import static java.time.LocalDateTime.now;

public class MiningRepo extends AbstractBehavior<MiningRepo.Message> {

    public MiningRepo(ActorContext<MiningRepo.Message> context) {
        super(context);
    }

    public static Behavior<MiningRepo.Message> create() {
        return Behaviors.setup(MiningRepo::new);
    }

    @Override
    public Receive<MiningRepo.Message> createReceive() {
        return newReceiveBuilder()
                .onMessage(Message.SaveMinerSummary.class, this::onSaveMinerSummary)
                .onMessage(Message.SaveMinerInitialization.class, this::onSaveMinerInitialization)
                .onMessage(Message.GetMinersInfo.class, this::getMinersInfo)
                .build();
    }

    private Behavior<Message> getMinersInfo(Message.GetMinersInfo getMinersInfo) {
        getContext().getLog().info("Getting miners info");

        try (Connection conn = DBFactory.getConnection()) {
            PreparedStatement preparedStatement = conn.prepareStatement("""
                    select miner_id, miner_ip, miner_port, desired_state from miner_info;
                    """);

            ResultSet resultSet = preparedStatement.executeQuery();
            List<MinersController.Miner> miners = new ArrayList<>();
            while (resultSet.next()) {
                String minerId = resultSet.getString("miner_id");
                String minerIp = resultSet.getString("miner_ip");
                int minerPort = resultSet.getInt("miner_port");
                String desiredState = resultSet.getString("desired_state");
                InetAddress minerIpAddr = InetAddress.getByName(minerIp);
                miners.add(new MinersController.Miner(minerId, minerIpAddr, minerPort, MinerState
                        .valueOf(desiredState.toUpperCase())));
            }
            getMinersInfo.replyTo.tell(new MinersController.Message.MinersInfo(miners));
        } catch (SQLException e) {
            getContext().getLog().error("Failed to get miners info", e);
        } catch (UnknownHostException e) {
            getContext().getLog().error("The resulted miner Ip from the database doesn't seems like a valid IP ", e);
        }
        return Behaviors.same();
    }

    private Behavior<MiningRepo.Message> onSaveMinerSummary(Message.SaveMinerSummary saveMinerSummary) {
        getContext().getLog().debug("Saving miner summary: {}", saveMinerSummary);

        try (Connection conn = DBFactory.getConnection()) {
            PreparedStatement preparedStatement = conn.prepareStatement("""
                    insert into miner_report (
                    miner_id,
                    miner_state,
                    miner_uptime,
                    miner_type,
                    average_hashrate,
                    instant_hashrate,
                    power_usage,
                    power_efficiency,
                    desired_state,
                    created_at,
                    chip_min_temp,
                    chip_max_temp,
                    pcb_min_temp,
                    pcb_max_temp,
                    temp_frequency_metric,
                    desired_state_retry_count
                    ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?,?,?);
                    """);

            preparedStatement.setString(1, saveMinerSummary.miner.id());
            preparedStatement.setString(2, saveMinerSummary.minerSummary().minerStatus().minerState());
            preparedStatement.setInt(3, saveMinerSummary.minerSummary().minerStatus().minerStateTime());
            preparedStatement.setString(4, saveMinerSummary.minerSummary().minerType());
            preparedStatement.setDouble(5, saveMinerSummary.minerSummary().averageHashRate());
            preparedStatement.setDouble(6, saveMinerSummary.minerSummary().instantHashRate());
            preparedStatement.setInt(7, saveMinerSummary.minerSummary().powerUsage());
            preparedStatement.setDouble(8, saveMinerSummary.minerSummary().powerEfficiency());
            preparedStatement.setString(9, saveMinerSummary.desiredState().name());
            preparedStatement.setTimestamp(10, Timestamp.valueOf(now()));
            preparedStatement.setInt(11, saveMinerSummary.minerSummary().chipTemp().min());
            preparedStatement.setInt(12, saveMinerSummary.minerSummary().chipTemp().max());
            preparedStatement.setInt(13, saveMinerSummary.minerSummary().pcbTemp().min());
            preparedStatement.setInt(14, saveMinerSummary.minerSummary().pcbTemp().max());

            PGobject jsonObject = new PGobject();
            jsonObject.setType("jsonb");
            jsonObject.setValue(saveMinerSummary.minerMetricsJson());
            preparedStatement.setObject(15, jsonObject);

            preparedStatement.setInt(16, saveMinerSummary.miner.retries());

            preparedStatement.executeUpdate();

        } catch (SQLException e) {
            getContext().getLog().error("Failed to save miner summary", e);
        }

        return Behaviors.same();
    }

    private Behavior<MiningRepo.Message> onSaveMinerInitialization(Message.SaveMinerInitialization saveMinerInitialization) {
        getContext().getLog().info("Saving miner initialization: {}", saveMinerInitialization);

        try (Connection conn = DBFactory.getConnection()) {
            PreparedStatement preparedStatement = conn.prepareStatement("""
                    INSERT INTO miner_info (miner_id, miner_ip, miner_port, desired_state, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT (miner_id) DO UPDATE SET miner_ip = EXCLUDED.miner_ip,
                    miner_port = EXCLUDED.miner_port,
                    desired_state = EXCLUDED.desired_state,
                    updated_at = EXCLUDED.created_at;
                    """);

            preparedStatement.setString(1, saveMinerInitialization.miner.id());
            preparedStatement.setString(2, saveMinerInitialization.miner.ipAddress()
                    .toString().replace("/", ""));
            preparedStatement.setInt(3, saveMinerInitialization.miner.port());
            preparedStatement.setString(4, saveMinerInitialization.desiredState());
            preparedStatement.setTimestamp(5, Timestamp.valueOf(now()));
            preparedStatement.executeUpdate();

        } catch (SQLException e) {
            getContext().getLog().error("Failed to save miner initialization", e);
        }

        return Behaviors.same();
    }

    public sealed interface Message {
        record SaveMinerInitialization(MinersController.Miner miner, String desiredState) implements Message {
        }


        record GetMinersInfo(ActorRef<MinersController.Message> replyTo) implements Message {
        }

        record SaveMinerSummary(MinersController.Miner miner, MinerSummaryRequest.MinerSummary minerSummary,
                                MinerState desiredState, String minerMetricsJson) implements Message {
        }
    }
}
