package sa.com.demaenergy;


import akka.actor.typed.ActorSystem;
import com.typesafe.config.ConfigFactory;
import org.flywaydb.core.Flyway;
import org.flywaydb.core.api.configuration.FluentConfiguration;
import org.flywaydb.core.api.output.MigrateResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;
import java.util.TimeZone;

public class Main {
    final static Logger logger = LoggerFactory.getLogger(Main.class);

    public static void main(String[] args) {
        TimeZone.setDefault(TimeZone.getTimeZone("Asia/Riyadh"));
        if (migrate(getProperties())) {
            ActorSystem.create(Guardian.create(), "Guardian", ConfigFactory.load());
        } else {
            System.exit(1);
        }
    }

    private static Properties getProperties() {
        Properties properties = new Properties();
        try {
            String configPath = System.getenv("FLYWAY_CONFIG_FILES");
            if (configPath == null) {
                configPath = "db/flyway.conf";
            }
            InputStream inputStream = Main.class.getClassLoader().getResourceAsStream(configPath);
            if (inputStream != null) {
                properties.load(inputStream);
            }
        } catch (IOException e) {
            logger.error("Failed to load flyway properties", e);
            throw new RuntimeException("Failed to load flyway properties", e);
        }
        return properties;
    }

    private static boolean migrate(Properties properties) {
        FluentConfiguration flywayConfig = Flyway.configure();
        if (!properties.isEmpty()) {
            flywayConfig = flywayConfig.configuration(properties);
        }

        flywayConfig = flywayConfig.envVars();
        Flyway flyway = flywayConfig.load();
        MigrateResult migrate = flyway.migrate();
        logger.info("Flyway migration result: {}", migrate.success ? "success" : "failed");
        migrate.warnings.forEach(logger::warn);
        return migrate.success;
    }
}
