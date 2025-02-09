package sa.com.demaenergy.mining.loadoptimizer.http;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.javadsl.ActorContext;
import akka.actor.typed.javadsl.Behaviors;
import akka.actor.typed.javadsl.Receive;
import com.fasterxml.jackson.databind.ObjectMapper; // Jackson library for JSON
import sa.com.demaenergy.mining.loadoptimizer.http.model.ResponseData;
import sa.com.demaenergy.mining.loadoptimizer.http.model.edMachineData;
import sa.com.demaenergy.mining.loadoptimizer.http.model.msMachineData;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.List;

public class FacadeActor extends AbstractBehavior<FacadeActor.Command> {

    public sealed interface Command {}

    public record GetEconomicDispatchOpt(ActorRef<?> replyTo, float energyPrice, List<edMachineData> MachineData) implements Command {} //TODO fix parameters
    public record GetMachineSelectionOpt(ActorRef<?> replyTo, float targetPower, float hashPrice, float energyPrice, List<msMachineData> MachineData) implements Command {} //TODO figure out how to insert machine data

    private final String flaskAppUrl = "http://localhost:5001"; // Base URL of your Flask app TODO: dot forget to put the right url

    public FacadeActor(ActorContext<Command> context) {
        super(context);
    }

    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
                .onMessage(GetEconomicDispatchOpt.class, this::onGetEconomicDispatchOpt)
                .onMessage(GetMachineSelectionOpt.class, this::onGetMachineSelectionOpt)
                .build();
    }

    private Behavior<Command> onGetEconomicDispatchOpt(GetEconomicDispatchOpt command) {
        String endpoint = "/ed/optimize"; // Flask endpoint for economic dispatch optimization
        ResponseData responseData = sendRequest(flaskAppUrl + endpoint, command);
        //TODO: handle what to do with response now!!!
        return Behaviors.same();
    }

    private Behavior<Command> onGetMachineSelectionOpt(GetMachineSelectionOpt command) {
        String endpoint = "/machine_selection/optimize"; // Flask endpoint for machine selection optimization
        ResponseData responseData = sendRequest(flaskAppUrl + endpoint, command);
        //TODO: handle what to do with response now!!!
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

    public static Behavior<Command> create() {
        return Behaviors.setup(FacadeActor::new);
    }
}
