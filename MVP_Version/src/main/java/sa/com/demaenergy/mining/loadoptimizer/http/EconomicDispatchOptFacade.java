package sa.com.demaenergy.mining.loadoptimizer.http;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.javadsl.ActorContext;
import akka.actor.typed.javadsl.Behaviors;
import akka.actor.typed.javadsl.Receive;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.ObjectMapper;
import sa.com.demaenergy.mining.loadoptimizer.EconomicDispatcher;
import sa.com.demaenergy.mining.loadoptimizer.http.model.edRequestResponseData;
import sa.com.demaenergy.mining.loadoptimizer.http.model.ResponseData;
import sa.com.demaenergy.mining.loadoptimizer.http.model.edMachineData;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.List;

public class EconomicDispatchOptFacade extends AbstractBehavior<EconomicDispatchOptFacade.Command> {


    public sealed interface Command {}

    public record GetEconomicDispatchOpt(ActorRef<?> replyTo, float energyPrice, List<edMachineData> MachineData) implements Command {}
    public record StartScheduler(ActorRef<Command> ref) implements Command{}
    public record FetchResponse(String requestID) implements Command{}

    private final String flaskAppUrl = "http://localhost:5001"; // Base URL of your Flask app TODO: dot forget to put the right url

    private final ActorRef<EconomicDispatcher.Message> economicDispatch;
    private String requestID;

    public EconomicDispatchOptFacade(ActorContext<Command> context, ActorRef<EconomicDispatcher.Message> economicDispatch) {
        super(context);
        context.getSelf().tell(new StartScheduler(context.getSelf()));
        this.economicDispatch = economicDispatch;
    }

    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
                .onMessage(GetEconomicDispatchOpt.class, this::onGetEconomicDispatchOpt)
                .onMessage(StartScheduler.class, this::startScheduler)
                .onMessage(FetchResponse.class, this::onFetchResponse)
                .build();
    }

    private Behavior<Command> startScheduler(Command command){

        return Behaviors.withTimers(timers -> {
            timers.startTimerWithFixedDelay(new FetchResponse(this.requestID),
                    java.time.Duration.ofSeconds(15));
            return Behaviors.same();
        });
    }

    private Behavior<Command> onFetchResponse(FetchResponse command) {
        String requestid = command.requestID;
        edRequestResponseData edRequestResponse = fetchResponseFromFlaskEndpoint(requestid);

        if ("Success".equals(edRequestResponse.status())) {

            //TODO: Store the response somewhere or give it back to requester
//            economicDispatch.tell();

            return Behaviors.stopped();
        }
        else { return Behaviors.same();}
    }

    private Behavior<Command> onGetEconomicDispatchOpt(GetEconomicDispatchOpt command) {
        String endpoint = "/ed/optimize"; // Flask endpoint for economic dispatch optimization
        ResponseData responseData = sendRequest(flaskAppUrl + endpoint, command);
        //TODO: handle what to do with response now!!!
        this.requestID = responseData.requestID();
        return Behaviors.same();
    }

    private ResponseData sendRequest(String urlString, Command command) {
        try {
            URL url = new URL(urlString);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setDoOutput(true);
            conn.setRequestProperty("Content-Type", "application/json");

            ObjectMapper mapper = new ObjectMapper();
            String json = mapper.writeValueAsString(command); // Directly serialize the command object

            byte[] out = json.getBytes(StandardCharsets.UTF_8);
            conn.setFixedLengthStreamingMode(out.length);
            conn.connect();
            try (OutputStream os = conn.getOutputStream()) {
                os.write(out);
            }


            if (conn.getResponseCode() == HttpURLConnection.HTTP_OK) {
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8))) {
                    ResponseData responseData = mapper.readValue(reader, ResponseData.class);

                    getContext().getLog().info(STR."Received response: \{responseData.requestID()}");

                    return responseData;


                }
            } else {
                getContext().getLog().error(STR."Non-OK response received: \{conn.getResponseCode()}");
                return new ResponseData("0");
            }

        } catch (Exception e) {
            getContext().getLog().error(STR."Error sending POST request to \{urlString}", e);
            return new ResponseData("0");
        }
    }


    private edRequestResponseData fetchResponseFromFlaskEndpoint(String requestID) {
        String url = "http://127.0.0.1:5001/ed/check_status/" + requestID;  // Update with your actual endpoint URL
        ObjectMapper mapper = new ObjectMapper();
        mapper.setSerializationInclusion(JsonInclude.Include.NON_NULL);

        try {
            URL obj = new URL(url);
            HttpURLConnection connection = (HttpURLConnection) obj.openConnection();
            connection.setRequestMethod("GET");

            if (connection.getResponseCode() == HttpURLConnection.HTTP_OK) {
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream(), StandardCharsets.UTF_8))) {
                    edRequestResponseData responseData = mapper.readValue(reader, edRequestResponseData.class);
                    System.out.println("Received response: " + responseData);  // or use logging based on your context
                    return responseData;
                }
            } else {
                System.out.println("GET request not worked");
                return null; // or throw an exception based on your error handling policy
            }
        } catch (Exception e) {
            System.err.println("Error during HTTP request: " + e.getMessage());
            return null; // or throw an exception based on your error handling policy
        }
    }


    public static Behavior<EconomicDispatchOptFacade.Command> create(ActorRef<EconomicDispatcher.Message> economicDispatch) {
        return Behaviors.setup(ctx -> new EconomicDispatchOptFacade(ctx, economicDispatch));
    }

}
