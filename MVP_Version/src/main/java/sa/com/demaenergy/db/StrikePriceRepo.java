package sa.com.demaenergy.db;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.javadsl.ActorContext;
import akka.actor.typed.javadsl.Behaviors;
import akka.actor.typed.javadsl.Receive;
import sa.com.demaenergy.mining.Bitcoin.StrikePriceActor;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

/*
 * Consider exactly once delivery
 * in case write to db failed, what should we do?
 * */
public class StrikePriceRepo extends AbstractBehavior<StrikePriceRepo.Message> {
    public StrikePriceRepo(ActorContext<Message> context) {
        super(context);
    }

    public static Behavior<Message> create() {
        return Behaviors.setup(StrikePriceRepo::new);
    }

    @Override
    public Receive<Message> createReceive() {
        return newReceiveBuilder()
                .onMessage(Message.GetConstants.class, this::onGetConstants)
                .onMessage(Message.SaveStrikePrice.class, this::onSaveStrikePrice)
                .build();
    }

    private Behavior<Message> onSaveStrikePrice(Message.SaveStrikePrice saveStrikePrice) {
        try (Connection conn = DBFactory.getConnection()) {
            getContext().getLog().info("Saving strike price: {}", saveStrikePrice.strikePrice);
            PreparedStatement preparedStatement = conn.prepareStatement("insert into strike_price (id, miner_hash_rate, miner_efficiency,hash_price ,strike_price, miner_id, created_at) " +
                    "values (gen_random_uuid(), ?, ?, ?, ?,?, NOW())");

            preparedStatement.setBigDecimal(1, saveStrikePrice.minersHashRate);
            preparedStatement.setBigDecimal(2, saveStrikePrice.minerEfficiency);
            preparedStatement.setDouble(3, saveStrikePrice.hashprice);
            preparedStatement.setBigDecimal(4, saveStrikePrice.strikePrice);
            preparedStatement.setString(5, saveStrikePrice.minerId);
            preparedStatement.execute();
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        return Behaviors.same();
    }

    private Behavior<Message> onGetConstants(Message.GetConstants getConstants) {
        getContext().getLog().info("Getting strike price constants ...");
        try (Connection conn = DBFactory.getConnection()) {
            PreparedStatement preparedStatement = conn.prepareStatement("select c1,c2,c3 from strike_price_calculation");

            ResultSet resultSet = preparedStatement.executeQuery();
            if (resultSet.next()) {
                double c1 = resultSet.getDouble("c1");
                double c2 = resultSet.getDouble("c2");
                double c3 = resultSet.getDouble("c3");
                getConstants.replyTo.tell(new StrikePriceActor.Command.GetConstantsResponse(c1, c2, c3));
            } else {
                throw new RuntimeException("No strike price constants found");
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }

        return Behaviors.same();
    }

    public sealed interface Message {
        record GetConstants(ActorRef<StrikePriceActor.Command> replyTo) implements Message {
        }

        record SaveStrikePrice(BigDecimal minersHashRate,
                               BigDecimal strikePrice,
                               BigDecimal minerEfficiency,
                               double hashprice, String minerId) implements Message {
        }
    }


}
