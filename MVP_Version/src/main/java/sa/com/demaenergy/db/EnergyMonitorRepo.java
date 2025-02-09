package sa.com.demaenergy.db;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.javadsl.ActorContext;
import akka.actor.typed.javadsl.Behaviors;
import akka.actor.typed.javadsl.Receive;
import sa.com.demaenergy.energymonitor.model.Dam;
import sa.com.demaenergy.energymonitor.model.EmergencyEventResponse.EmergencyEvent;
import sa.com.demaenergy.energymonitor.model.PLCReading;
import sa.com.demaenergy.energymonitor.model.PredictedPrices;

import java.math.BigDecimal;
import java.sql.*;
import java.util.List;

import static java.time.LocalDateTime.now;
import static sa.com.demaenergy.db.EnergyMonitorRepo.Message.*;

/*
 * Consider exactly once delivery
 * in case write to db failed, what should we do?
 * */
public class EnergyMonitorRepo extends AbstractBehavior<EnergyMonitorRepo.Message> {
    public EnergyMonitorRepo(ActorContext<Message> context) {
        super(context);
    }

    public static Behavior<Message> create() {
        return Behaviors.setup(EnergyMonitorRepo::new);
    }

    @Override
    public Receive<Message> createReceive() {
        return newReceiveBuilder()
                .onMessage(GetRTMPrice.class, this::onGetEnergyPrice)
                .onMessage(SaveRTMPrice.class, this::onSaveRTMPrice)
                .onMessage(GetEmergencyStatus.class, this::onGetEnergyUsage)
                .onMessage(SaveEmergencyStatus.class, this::onSaveEmergencyStatus)
                .onMessage(SaveWattageReading.class, this::onSaveWattageReading)
                .onMessage(SaveMarketPredictions.class, this::onSaveMarketPredictions)
                .onMessage(SaveDAMPrice.class, this::onSaveDamPrice)
                .onMessage(GetMostRecentMarketPrediction.class, this::onGetMostRecentMarketPrediction)
                .onMessage(GetAPI.class, this::onGetAPI)
                .onMessage(GetPLC.class, this::onGetPLC)
                .onMessage(GetDAMPrice.class, this::onGetDAM)
                .build();
    }

    private Behavior<Message> onSaveEmergencyStatus(SaveEmergencyStatus saveEmergencyStatus) {
        getContext().getLog().info("Saving emergency event");
        try (Connection conn = DBFactory.getConnection()) {
            PreparedStatement preparedStatement = conn.prepareStatement("insert into emergency_events (active, created_at, api_id) values (?, ?, ?)");
            preparedStatement.setInt(1, saveEmergencyStatus.emergencyEvent.active());
            preparedStatement.setTimestamp(2, Timestamp.valueOf(now()));
            preparedStatement.setInt(3, saveEmergencyStatus.apiID);
            preparedStatement.execute();
        } catch (SQLException e) {
            getContext().getLog().error("Error saving wattage meter to Database", e);
            throw new RuntimeException(e);
        }
        return Behaviors.same();
    }

    private Behavior<Message> onSaveWattageReading(SaveWattageReading saveWattageReading) {
        getContext().getLog().info("Saving Wattage Meter: {}", saveWattageReading.plcReading());

        try (Connection conn = DBFactory.getConnection()) {
            PreparedStatement preparedStatement = conn.prepareStatement("insert into wattage_meter (wattage, created_at, plc_id) values (?, ?, ?)");
            preparedStatement.setInt(1, saveWattageReading.plcReading().wattage());
            preparedStatement.setTimestamp(2, Timestamp.valueOf(now()));
            preparedStatement.setInt(3, saveWattageReading.plcID());
            preparedStatement.execute();
        } catch (SQLException e) {
            getContext().getLog().error("Error saving wattage meter to Database", e);
            throw new RuntimeException(e);
        }
        return Behaviors.same();
    }

    private Behavior<Message> onSaveMarketPredictions(SaveMarketPredictions saveMarketPredictions) {
        getContext().getLog().info("Saving Market Predictions: {}", saveMarketPredictions.predictedPrices());
        try (Connection conn = DBFactory.getConnection()) {
            for (PredictedPrices predictedPrice: saveMarketPredictions.predictedPrices){
                PreparedStatement preparedStatement = conn.prepareStatement("insert into market_predictions (rtd_datetime, price, price_5, price_10, price_15, price_20, price_25, price_30, price_35, price_40, price_45, price_50, price_55, created_at) " +
                        "values (?,?,?,?,?,?,?,?,?,?,?,?,?, ?)");
                preparedStatement.setTimestamp(1, predictedPrice.rtd_datetime());
                preparedStatement.setFloat(2, predictedPrice.price());
                preparedStatement.setFloat(3, predictedPrice.price_5());
                preparedStatement.setFloat(4, predictedPrice.price_10());
                preparedStatement.setFloat(5, predictedPrice.price_15());
                preparedStatement.setFloat(6, predictedPrice.price_20());
                preparedStatement.setFloat(7, predictedPrice.price_25());
                preparedStatement.setFloat(8, predictedPrice.price_30());
                preparedStatement.setFloat(9, predictedPrice.price_35());
                preparedStatement.setFloat(10, predictedPrice.price_40());
                preparedStatement.setFloat(11, predictedPrice.price_45());
                preparedStatement.setFloat(12, predictedPrice.price_50());
                preparedStatement.setFloat(13, predictedPrice.price_55());
                preparedStatement.setTimestamp(14, Timestamp.valueOf(now()));
                preparedStatement.execute();
            }
        } catch (SQLException e) {
            getContext().getLog().error("Error saving market predictions to Database", e);
            throw new RuntimeException(e);
        }
        return Behaviors.same();
    }

    private Behavior<Message> onSaveRTMPrice(SaveRTMPrice saveRTMPrice) {
        try (Connection conn = DBFactory.getConnection()) {
            getContext().getLog().info("Saving RTM price: {}", saveRTMPrice.price());
            PreparedStatement preparedStatement = conn.prepareStatement("insert into market_prices (price, created_at, api_id) " +
                    "values (?, ?, ?)");

            preparedStatement.setBigDecimal(1, saveRTMPrice.price());
            preparedStatement.setTimestamp(2, Timestamp.valueOf(now()));
            preparedStatement.setInt(3, saveRTMPrice.apiID());
            preparedStatement.execute();
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        return Behaviors.same();
    }

    private Behavior<Message> onSaveDamPrice(SaveDAMPrice saveDAMPrice) {
        try (Connection conn = DBFactory.getConnection()) {
            getContext().getLog().info("Saving DAM price: {}", saveDAMPrice.dam());
            PreparedStatement preparedStatement = conn.prepareStatement("insert into day_ahead_market (bid_id, start_time, end_time, settlement_point, awarded_mwh, spp, created_at) " +
                    "values (?, ?, ?, ?, ?, ?, ?)");
            preparedStatement.setString(1, saveDAMPrice.dam().bidId());
            preparedStatement.setTimestamp(2, saveDAMPrice.dam().startTime());
            preparedStatement.setTimestamp(3, saveDAMPrice.dam().endTime());
            preparedStatement.setString(4, saveDAMPrice.dam().settlementPoint());
            preparedStatement.setFloat(5, saveDAMPrice.dam().awardedMwh());
            preparedStatement.setFloat(6, saveDAMPrice.dam().spp());
            preparedStatement.setTimestamp(7, Timestamp.valueOf(now()));
            preparedStatement.execute();
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        return Behaviors.same();
    }

    private Behavior<Message> onGetAPI(GetAPI getAPI) {
        try (Connection conn = DBFactory.getConnection()) {
            PreparedStatement preparedStatement = conn.prepareStatement("select * from apis where id = ?");
            preparedStatement.setInt(1, getAPI.ID);
            ResultSet resultSet = preparedStatement.executeQuery();
            if (resultSet.next()) {
                String api = resultSet.getString("path");
                String endpoint = resultSet.getString("endpoint");
                String apiKey = resultSet.getString("api_key");
                int delay = resultSet.getInt("delay");
                getContext().getLog().info("api: {}", api);
                getAPI.replyTo().tell(new Response.APIResponse(api, endpoint, apiKey, delay));
            } else {
                getContext().getLog().warn("No api found");
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        return Behaviors.same();
    }

    private Behavior<Message> onGetPLC(GetPLC getPLC) {
        try (Connection conn = DBFactory.getConnection()) {
            PreparedStatement preparedStatement = conn.prepareStatement("select * from plc where id = ?");
            preparedStatement.setInt(1, getPLC.ID);
            ResultSet resultSet = preparedStatement.executeQuery();
            if (resultSet.next()) {
                String plcIP = resultSet.getString("ip");
                int plcPort = resultSet.getInt("port");
                int plcRegister = resultSet.getInt("register");
                int delay = resultSet.getInt("delay");
                getContext().getLog().info("plc: {}", plcIP);
                getPLC.replyTo().tell(new Response.PLCResponse(plcIP, plcPort, plcRegister, delay));
            } else {
                getContext().getLog().warn("No plc found");
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        return Behaviors.same();
    }

    private Behavior<Message> onGetMostRecentMarketPrediction(GetMostRecentMarketPrediction getMostRecentMarketPrediction){
        try (Connection conn = DBFactory.getConnection()) {
            ResultSet resultSet = conn.prepareStatement("select max(rtd_datetime) as rtd_datetime from market_predictions")
                    .executeQuery();
            if (resultSet.next() && resultSet.getTimestamp("rtd_datetime") != null) {
                getContext().getLog().info("Most recent market prediction date: {}", resultSet.getTimestamp("rtd_datetime"));
                PredictedPrices predictedPrices = new PredictedPrices(
                        resultSet.getTimestamp("rtd_datetime"),
                        0.0f,
                        0.0f,
                        0.0f,
                        0.0f,
                        0.0f,
                        0.0f,
                        0.0f,
                        0.0f,
                        0.0f,
                        0.0f,
                        0.0f,
                        0.0f
                );
                getMostRecentMarketPrediction.replyTo().tell(new Response.MostRecentMarketPredictionResponse(predictedPrices));
            } else {
                getContext().getLog().warn("No market predictions found");
                PredictedPrices origin = new PredictedPrices(
                        Timestamp.valueOf("1998-04-11 20:15:00"),
                        0.0f,
                        0.0f,
                        0.0f,
                        0.0f,
                        0.0f,
                        0.0f,
                        0.0f,
                        0.0f,
                        0.0f,
                        0.0f,
                        0.0f,
                        0.0f);
                getMostRecentMarketPrediction.replyTo()
                        .tell(new Response.MostRecentMarketPredictionResponse(origin));
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        return Behaviors.same();
    }

    private Behavior<Message> onGetEnergyUsage(GetEmergencyStatus getEmergencyStatus) {
        return null;
    }

    private Behavior<Message> onGetEnergyPrice(GetRTMPrice getRTMPrice) {
        try (Connection conn = DBFactory.getConnection()) {
            ResultSet resultSet = conn.prepareStatement("select price, created_at from rtm_price") //isnt it called market_prices?
                    .executeQuery();
            if (resultSet.next()) {
                BigDecimal price = resultSet.getBigDecimal("price");
                Timestamp timestamp = resultSet.getTimestamp("created_at");
                getContext().getLog().info("price: {}, timestamp: {}", price, timestamp);
                getRTMPrice.replyTo().tell(new Response.RTMPriceResponse(price, timestamp));
            } else {
                getContext().getLog().warn("No price found");
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        return Behaviors.same();
    }

    private Behavior<Message> onGetDAM(GetDAMPrice getDAMPrice) {
        getContext().getLog().info("Fetching DAM price {}", now());
        try (Connection conn = DBFactory.getConnection()) {
            ResultSet resultSet = conn.prepareStatement("select id, bid_id, start_time, " +
                            "end_time, settlement_point, awarded_mwh, spp, created_at from day_ahead_market " +
                            "where '" + now() + "' between start_time and end_time")
                    .executeQuery();
            if (resultSet.next()) {
                Dam dam = new Dam(
                        resultSet.getString("id"),
                        resultSet.getString("bid_id"),
                        resultSet.getTimestamp("start_time"),
                        resultSet.getTimestamp("end_time"),
                        resultSet.getString("settlement_point"),
                        resultSet.getFloat("awarded_mwh"),
                        resultSet.getFloat("spp"),
                        resultSet.getTimestamp("created_at"));
                getDAMPrice.replyTo().tell(new Response.DAMPriceResponse(dam));
            } else {
                getDAMPrice.replyTo().tell(new Response.DAMPriceResponse(null));
                getContext().getLog().warn("No dam price found");
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        return Behaviors.same();
    }

    public sealed interface Message {
        record GetRTMPrice(ActorRef<Response.RTMPriceResponse> replyTo) implements Message {
        }

        sealed interface Response {
            record RTMPriceResponse(BigDecimal price, Timestamp timestamp) implements Response {

            }

            record APIResponse(String api, String endpoint, String apiKey, int delay) implements Response {
            }
            record PLCResponse(String plcIP, int plcPort, int plcRegister, int delay) implements Response {
            }
            record MostRecentMarketPredictionResponse(PredictedPrices predictedPrices) implements Response {
            } // use this to determine scraping date for market predictions
            record DAMPriceResponse(Dam dam) implements Response {
            }
        }

        record SaveRTMPrice(BigDecimal price, int apiID) implements Message {
        }

        record GetEmergencyStatus() implements Message {
        }

        record GetAPI(ActorRef<Response.APIResponse> replyTo, int ID) implements Message {
        }

        record GetPLC(ActorRef<Response.PLCResponse> replyTo, int ID) implements Message {
        }

        record SaveEmergencyStatus(EmergencyEvent emergencyEvent, int apiID) implements Message {
        }

        record SaveWattageReading(PLCReading plcReading, int plcID) implements Message {
        }

        record SaveMarketPredictions(List<PredictedPrices> predictedPrices) implements Message {
        }
        record GetMostRecentMarketPrediction(ActorRef<Response.MostRecentMarketPredictionResponse> replyTo) implements Message {
        }
        record GetDAMPrice(ActorRef<Response.DAMPriceResponse> replyTo) implements Message {
        }
        record SaveDAMPrice(Dam dam) implements Message {
        }
    }
}
