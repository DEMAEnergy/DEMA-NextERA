package sa.com.demaenergy.energymonitor;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.*;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.select.Elements;
import sa.com.demaenergy.db.EnergyMonitorRepo;
import sa.com.demaenergy.energymonitor.model.PredictedPrices;

import java.io.IOException;
import java.sql.Timestamp;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.time.Duration;
import java.util.*;

public class MarketPrediction extends AbstractBehavior<MarketPrediction.Command> {
    private final ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo;
    private final String url = getContext().getSystem().settings().config().getString("ercot.prices-url");
    private final SimpleDateFormat inputFormat = new SimpleDateFormat("MM/dd/yyyy hh:mm:ss");
    private final SimpleDateFormat outputFormat = new SimpleDateFormat("yyyy-MM-dd hh:mm:ss");
    private final Map<String, String> headers = Map.of("Referer", "https://www.google.com:",
            "User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    );
    private List<PredictedPrices> predictions = new ArrayList<>();
    public sealed interface Command {
    }

    public record MarketPredictionState(ActorRef<EnergyMonitor.Command> replyTo, UUID requestID) implements Command {
    }

    private record PredictMarket() implements Command {
    }

    private record InitiateDBCommit(List<PredictedPrices> predictions) implements Command {
    }
    private record CommitsPredictionToDB(
            EnergyMonitorRepo.Message.Response.MostRecentMarketPredictionResponse response, List<PredictedPrices> predictions) implements Command {
    }
    private record MaxScrapedDateFailure(Throwable th) implements Command {
    }

    private MarketPrediction(ActorContext<Command> context, TimerScheduler<Command> timers, ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo) {
        super(context);
        this.energyMonitorRepo = energyMonitorRepo;
        timers.startTimerWithFixedDelay(new PredictMarket(), Duration.ofSeconds(100),Duration.ofMinutes(5));
    }

    public static Behavior<Command> create(ActorRef<EnergyMonitorRepo.Message> energyMonitorRepo) {
        return Behaviors.withTimers(timers -> Behaviors.setup(ctx -> new MarketPrediction(ctx, timers, energyMonitorRepo)));
    }

    private Behavior<Command> scrapeMarketPrediction(PredictMarket command) {
        List<PredictedPrices> predictions = new ArrayList<>();
        Document doc;
        try {
            doc = Jsoup.connect(url).headers(headers).get();
        } catch (IOException e) {
            getContext().getLog().error("Error fetching energy price: {}", e.getMessage());
            throw new RuntimeException(e);
        }
        Elements table = doc.select("table");
        Elements cols = table.select("td.headerValueClass");
        Elements rows = table.select("td.labelClassCenter");

        for (int i = 0; i < rows.size(); i += cols.size()) {
            try {
                Date currentTime = inputFormat.parse(rows.get(i).text());
                String parsedTime = outputFormat.format(currentTime);
                PredictedPrices prediction = new PredictedPrices(
                        Timestamp.valueOf(parsedTime),
                        Float.parseFloat(rows.get(i + 1).text()),
                        Float.parseFloat(rows.get(i + 2).text()),
                        Float.parseFloat(rows.get(i + 3).text()),
                        Float.parseFloat(rows.get(i + 4).text()),
                        Float.parseFloat(rows.get(i + 5).text()),
                        Float.parseFloat(rows.get(i + 6).text()),
                        Float.parseFloat(rows.get(i + 7).text()),
                        Float.parseFloat(rows.get(i + 8).text()),
                        Float.parseFloat(rows.get(i + 9).text()),
                        Float.parseFloat(rows.get(i + 10).text()),
                        Float.parseFloat(rows.get(i + 11).text()),
                        Float.parseFloat(rows.get(i + 12).text())
                );
                predictions.add(prediction);
            } catch (ParseException e) {
                getContext().getLog().error("Error parsing date: {}", e.getMessage());
                throw new RuntimeException(e);
            }
        }
        this.predictions = Collections.unmodifiableList(predictions);
        getContext().getSelf().tell(new InitiateDBCommit(Collections.unmodifiableList(predictions)));
        return Behaviors.same();
    }

    private Behavior<Command> marketPredictionState(MarketPredictionState command) {
        command.replyTo.tell(new EnergyMonitor.MarketPredictionResponse(Collections.unmodifiableList(predictions),
                command.requestID));
        return Behaviors.same();
    }

    private Behavior<Command> initiateDBCommit(InitiateDBCommit command) {
        getContext().ask(
                EnergyMonitorRepo.Message.Response.MostRecentMarketPredictionResponse.class,
                energyMonitorRepo,
                Duration.ofSeconds(5),
                EnergyMonitorRepo.Message.GetMostRecentMarketPrediction::new,
                (response, throwable) -> {
                    if (response != null) {
                        return new CommitsPredictionToDB(response, Collections.unmodifiableList(command.predictions));
                    } else {
                        getContext().getLog().error("Error fetching most recent market prediction: {}", throwable.getMessage());
                        return new MaxScrapedDateFailure(throwable);
                    }
                });
        return Behaviors.same();
    }

    private Behavior<Command> commitPredictionsToDB(CommitsPredictionToDB command) {
        if (command.predictions.isEmpty()) {
            getContext().getLog().info("No predictions to commit to db");
            return Behaviors.same();
        }
        // filter out predictions that are already in the db
        List<PredictedPrices> newPredictions = new ArrayList<>();
        for (PredictedPrices prediction : command.predictions) {
            if (prediction.rtd_datetime().after(command.response.predictedPrices().rtd_datetime())) {
                newPredictions.add(prediction);
            }
        }
        if (newPredictions.isEmpty()) {
            getContext().getLog().info("No new predictions to commit to db");
            return Behaviors.same();
        }
        getContext().getLog().info("Committing {} new predictions to db", newPredictions.size());
        energyMonitorRepo.tell(new EnergyMonitorRepo.Message.SaveMarketPredictions(newPredictions));
        return Behaviors.same();
    }

    private Behavior<Command> handleMaxScrapedDateFailure(MaxScrapedDateFailure command) {
        getContext().getLog().error("Error fetching most recent market prediction: {}", command.th.getMessage());
        return Behaviors.same();
    }


    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
                .onMessage(PredictMarket.class, this::scrapeMarketPrediction)
                .onMessage(MarketPredictionState.class, this::marketPredictionState)
                .onMessage(InitiateDBCommit.class, this::initiateDBCommit)
                .onMessage(CommitsPredictionToDB.class, this::commitPredictionsToDB)
                .onMessage(MaxScrapedDateFailure.class, this::handleMaxScrapedDateFailure)
                .build();
    }
}

