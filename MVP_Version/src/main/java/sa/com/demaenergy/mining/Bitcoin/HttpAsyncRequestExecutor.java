package sa.com.demaenergy.mining.Bitcoin;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.javadsl.ActorContext;
import akka.actor.typed.javadsl.Behaviors;
import akka.actor.typed.javadsl.Receive;
import akka.http.javadsl.Http;
import akka.http.javadsl.marshallers.jackson.Jackson;
import akka.http.javadsl.model.HttpRequest;
import akka.http.javadsl.model.HttpResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.fasterxml.jackson.datatype.jsr310.deser.LocalDateTimeDeserializer;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.CompletionStage;

public class HttpAsyncRequestExecutor<Reply extends A, A> extends AbstractBehavior<HttpAsyncRequestExecutor.Command> {

    private final ActorRef<A> replyTo;
    private final Class<Reply> replyClass;
    ObjectMapper objectMapper;

    public interface Command {

    }

    final Http http = Http.get(this.getContext().getSystem());

    public static <R extends A, A> Behavior<Command> create(ActorRef<A> replyTo, HttpRequest request, Class<R> replyClass) {
        return Behaviors.setup(context -> new HttpAsyncRequestExecutor<R, A>(context, replyTo, request, replyClass));
    }

    public HttpAsyncRequestExecutor(ActorContext<Command> context, ActorRef<A> replyTo, HttpRequest request,
                                    Class<Reply> replyClass) {

        super(context);
        this.replyTo = replyTo;
        this.replyClass = replyClass;

        this.objectMapper = new ObjectMapper();
//        2024-03-01T01:30:00+00:00
        LocalDateTimeDeserializer localDateTimeDeserializer = new LocalDateTimeDeserializer(DateTimeFormatter
                .ofPattern("yyyy-MM-dd'T'HH:mm:ss+hh:mm"));
        objectMapper.registerModule(new JavaTimeModule().addDeserializer(LocalDateTime.class, localDateTimeDeserializer));




        this.fetch(request);
    }


    record ResponseCommand(HttpResponse response) implements Command {
    }

    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
                .onMessage(ResponseCommand.class, this::onResponse)
                .onMessage(WrappedReply.class, this::onResponse)
                .build();
    }

    private Behavior<Command> onResponse(WrappedReply<Reply> wrappedReply) {
        getContext().getLog().info(STR."Response: \{wrappedReply.msg}");
        this.replyTo.tell(wrappedReply.msg);
        return Behaviors.stopped();
    }


    public record WrappedReply<R>(R msg) implements Command {
    }

    Behavior<Command> onResponse(ResponseCommand response) {
        // do something with the response
        this.getContext().getLog().info(STR."Response: \{response.response}");


        this.getContext().pipeToSelf(
                Jackson.unmarshaller(objectMapper, replyClass).unmarshal(response.response.entity(), this.getContext().getSystem()),
                (msg, throwable) -> {
                    if (throwable != null) {
                        throw new RuntimeException(throwable);
                    }
                    return new WrappedReply<Reply>(msg);
                }
        );
        return Behaviors.same();
    }

    private void fetch(HttpRequest request) {
        CompletionStage<HttpResponse> responseFuture = http.singleRequest(request);
        responseFuture.thenApply(response -> {
                    getContext().getSelf().tell(new ResponseCommand(response));
                    return response;
                }
        );

    }

}