package sa.com.demaenergy.mining.Bitcoin;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.javadsl.ActorContext;
import akka.actor.typed.javadsl.Behaviors;
import akka.actor.typed.javadsl.Receive;
import akka.http.javadsl.model.HttpHeader;
import akka.http.javadsl.model.HttpRequest;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.time.ZonedDateTime;
import java.util.HashMap;
import java.util.Map;

import static akka.http.javadsl.model.ContentTypes.APPLICATION_JSON;
import static java.util.List.of;
import static sa.com.demaenergy.mining.Bitcoin.StrikePriceActor.Command.*;


public class HashPrice extends AbstractBehavior<HashPrice.Command> {
    private static final String API_KEY = "hi.45a3e0bc321ebe41a353533a54ffc6d6";
    private static final String API_URL = "https://api.hashrateindex.com/graphql";
    private final ActorRef<StrikePriceActor.Command> replyTo;

    public HashPrice(ActorContext<Command> context, ActorRef<StrikePriceActor.Command> replyTo) {
        super(context);
        this.replyTo = replyTo;
    }

    public static Behavior<Command> create(ActorRef<StrikePriceActor.Command> replyTo) {
        return Behaviors.setup(context -> new HashPrice(context, replyTo));
    }

    public interface Command {
    }

    public record GetHashPriceRequest() implements Command {
    }

    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
                .onMessage(GetHashPriceRequest.class, this::handleHashPriceRequest)
                .onMessage(HashPriceUSD.class, this::onHashPriceUSD)
                .build();
    }

    private Behavior<Command> onHashPriceUSD(HashPriceUSD hashPriceUSD) {
        getContext().getLog().info("HashPriceUSD: {}", hashPriceUSD);
        var latest = hashPriceUSD.data().getHashprice().nodes()[hashPriceUSD.data().getHashprice().nodes().length - 1];
        getContext().getLog().info("Latest hash price: {}", latest.usdHashprice());
        replyTo.tell(new GetHashPriceResponse(latest.usdHashprice()));

        return Behaviors.stopped();
    }

    private Behavior<Command> handleHashPriceRequest(GetHashPriceRequest request) {

        ObjectMapper objectMapper = new ObjectMapper();
        String field = "usdHashprice";
        String query = """
                query get_hashprice($inputInterval: ChartsInterval!, $first: Int) {
                    getHashprice(inputInterval: $inputInterval, first: $first) {
                        nodes {
                            timestamp
                            %s
                        }
                    }
                }
                """.formatted(field);

        Map<String, Object> params = new HashMap<>();
        params.put("inputInterval", "_1_DAY");
        params.put("first", 10000);

        String requestBody;
        try {
            requestBody = objectMapper.writeValueAsString(Map.of("query", query, "variables", params));
        } catch (Exception e) {
            getContext().getLog().error("Error serializing request body", e);
            return null;
        }
        getContext().getLog().info("Request body: {}", requestBody);

        HttpRequest httpRequest = HttpRequest.POST(API_URL)
                .withEntity(APPLICATION_JSON, requestBody)
                .withHeaders(of(
                        HttpHeader.parse("Content-Type", "application/json"),
                        HttpHeader.parse("x-hi-api-key", API_KEY))
                );

        getContext().spawnAnonymous(
                HttpAsyncRequestExecutor.create(
                        getContext().getSelf(),
                        httpRequest,
                        HashPriceUSD.class)
        );

        return Behaviors.same();
    }

    private record HashPriceUSD(
            Data data
    ) implements HashPrice.Command {
        private record Data(
                GetHashprice getHashprice
        ) {
            private record GetHashprice(
                    Node[] nodes
            ) {
                private record Node(
                        ZonedDateTime timestamp,
                        double usdHashprice
                ) {
                }
            }
        }
    }
}
