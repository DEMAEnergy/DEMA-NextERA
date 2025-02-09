package sa.com.demaenergy;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.javadsl.ActorContext;
import akka.actor.typed.javadsl.Behaviors;
import akka.actor.typed.javadsl.Receive;
import com.typesafe.config.Config;
import sa.com.demaenergy.db.DBFactory;
import sa.com.demaenergy.db.EnergyMonitorRepo;
import sa.com.demaenergy.db.MiningRepo;
import sa.com.demaenergy.energymonitor.DayAheadMarket;
import sa.com.demaenergy.energymonitor.EnergyMonitor;
import sa.com.demaenergy.mining.loadoptimizer.MiningLoadOptimizer;
import sa.com.demaenergy.mining.manager.MinersController;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class SiteActor extends AbstractBehavior<SiteActor.Command> {

    public interface Command{}

    private int locationID;

    public static Behavior<Command> create(int location) {
        return Behaviors.setup(
                ctx -> new SiteActor(ctx,location)
        );
    }

    public SiteActor(ActorContext<SiteActor.Command> context,int location) {
        super(context);
        this.locationID = location;

//        todo: fetch apis related to site from api table

        // Inline logic to fetch APIs related to the site from the API table
        List<ApiDetails> siteApis = new ArrayList<>();

        // Load configuration
        Config config = getContext().getSystem().settings().config();
        String url = config.getString("datasource.url");
        String user = config.getString("datasource.username");
        String password = config.getString("datasource.password");


        try (Connection connection = DriverManager.getConnection(url, user, password)) {
            String query = "SELECT path, endpoint, api_key, request_type, payload FROM apis WHERE location = ?";
            try (PreparedStatement statement = connection.prepareStatement(query)) {
                statement.setInt(1, location);
                try (ResultSet resultSet = statement.executeQuery()) {
                    while (resultSet.next()) {
                        String path = resultSet.getString("path");
                        String endpoint = resultSet.getString("endpoint");
                        String apiKey = resultSet.getString("api_key");
                        String requestType = resultSet.getString("request_type");
                        String payload = resultSet.getString("payload");
                        siteApis.add(new ApiDetails(path, endpoint, apiKey, requestType, payload));
                    }
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
            // Handle exceptions
        }

        // Print fetched APIs (for demonstration purposes)
        siteApis.forEach(api -> System.out.println("Fetched API: " + api));

        //TODO: figure out what to do with apis


        //        todo: fetch site network
        try (Connection connection = DriverManager.getConnection(url, user, password)) {

            String query = "SELECT path FROM site_network WHERE location = ?";
            try (PreparedStatement statement = connection.prepareStatement(query)){
                statement.setInt(1,location);
                try (ResultSet resultSet = statement.executeQuery()){
                    while (resultSet.next()){
                        String network_path = resultSet.getString("path");
                    }
                }
            }
        }
        catch (Exception e) {
            e.printStackTrace();
            // Handle exceptions
        }




//        TODO: these component should be specific to this site, Review
        ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo = context.spawn(EnergyMonitorRepo.create(),
                "EnergyMonitorRepo");
        ActorRef<EnergyMonitor.Command> energyMonitor = context.spawn(EnergyMonitor.create(energyMonitorRepo), "EnergyMonitor");
        ActorRef<DayAheadMarket.Command> dayAheadMarket = context.spawn(DayAheadMarket.create(energyMonitorRepo), "DayAheadMarket");
        ActorRef<MiningRepo.Message> miningRepo = context.spawn(MiningRepo.create(), "MiningRepo");
        ActorRef<MinersController.Message> minersController = context.spawn(MinersController.create(miningRepo), "MinersController");
        ActorRef<MiningLoadOptimizer.Message> miningLoadOptimizer = context.spawn(MiningLoadOptimizer.create(energyMonitor, dayAheadMarket, minersController), "MiningLoadOptimizer");
    }

    @Override
    public Receive<SiteActor.Command> createReceive() {
        return null;
    }

    // Define a class to hold API details
    public static class ApiDetails {
        public final String path;
        public final String endpoint;
        public final String apiKey;
        public final String requestType;
        public final String payload;

        public ApiDetails(String path, String endpoint, String apiKey, String requestType, String payload) {
            this.path = path;
            this.endpoint = endpoint;
            this.apiKey = apiKey;
            this.requestType = requestType;
            this.payload = payload;
        }

        @Override
        public String toString() {
            return "ApiDetails{" +
                    "path='" + path + '\'' +
                    ", endpoint='" + endpoint + '\'' +
                    ", apiKey='" + apiKey + '\'' +
                    ", requestType='" + requestType + '\'' +
                    ", payload='" + payload + '\'' +
                    '}';
        }
    }
}
