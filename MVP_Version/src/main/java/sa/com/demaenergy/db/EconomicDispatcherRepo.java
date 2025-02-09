package sa.com.demaenergy.db;

import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.javadsl.ActorContext;
import akka.actor.typed.javadsl.Behaviors;
import akka.actor.typed.javadsl.Receive;
import com.google.gson.Gson;
import org.postgresql.util.PGobject;
import sa.com.demaenergy.db.EconomicDispatcherRepo.Message.SaveEconomicDispatcherMetadata;
import sa.com.demaenergy.mining.Bitcoin.StrikePriceActor.StrikePrice;
import sa.com.demaenergy.mining.loadoptimizer.EconomicDispatcher.Message.MinersPowerUsageResponse.PowerUsage;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.util.List;

/*
 * Consider exactly once delivery
 * in case write to db failed, what should we do?
 * */
public class EconomicDispatcherRepo extends AbstractBehavior<EconomicDispatcherRepo.Message> {
    public EconomicDispatcherRepo(ActorContext<Message> context) {
        super(context);
    }

    public static Behavior<Message> create() {
        return Behaviors.setup(EconomicDispatcherRepo::new);
    }

    @Override
    public Receive<Message> createReceive() {
        return newReceiveBuilder()
                .onMessage(SaveEconomicDispatcherMetadata.class, this::onSaveEconomicDispatcherMetadata)
                .build();
    }

    private Behavior<Message> onSaveEconomicDispatcherMetadata(SaveEconomicDispatcherMetadata saveEconomicDispatcherMetadata) {
        getContext().getLog().info("Saving economic dispatcher metadata: {}", saveEconomicDispatcherMetadata);
        String minerspowerusagesJson = new Gson().toJson(saveEconomicDispatcherMetadata.minersPowerUsages);
        String strikepricesJson = new Gson().toJson(saveEconomicDispatcherMetadata.strikePrices);

        try (Connection conn = DBFactory.getConnection()) {
            PreparedStatement preparedStatement = conn.prepareStatement("""
                    insert into economic_dispatcher (
                    id,
                    rtm_price,
                    optimizedpowertarget,
                    strikeprices,
                    minerspowerusages,
                    created_at) values (gen_random_uuid(), ?, ?, ?, ?, NOW());
                    """);

            preparedStatement.setBigDecimal(1, saveEconomicDispatcherMetadata.RTM_Price);
            preparedStatement.setBigDecimal(2, saveEconomicDispatcherMetadata.optimizedPowerTarget);
            preparedStatement.setObject(3, getPGJsonObject(strikepricesJson));
            preparedStatement.setObject(4, getPGJsonObject(minerspowerusagesJson));

            preparedStatement.execute();

            if (preparedStatement.getUpdateCount() != 1) {
                throw new RuntimeException("Failed to save economic dispatcher metadata");
            }


        } catch (SQLException e) {
            throw new RuntimeException(e);

        }

        return Behaviors.same();
    }

    private static PGobject getPGJsonObject(String strikepricesJson) throws SQLException {
        PGobject jsonObject = new PGobject();
        jsonObject.setType("jsonb");
        jsonObject.setValue(strikepricesJson);
        return jsonObject;
    }

    public sealed interface Message {
        record SaveEconomicDispatcherMetadata(BigDecimal RTM_Price,
                                              List<StrikePrice> strikePrices,
                                              List<PowerUsage> minersPowerUsages,
                                              BigDecimal optimizedPowerTarget) implements Message {
        }
    }


}
