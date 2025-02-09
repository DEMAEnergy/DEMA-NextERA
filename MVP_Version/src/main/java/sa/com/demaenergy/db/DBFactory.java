package sa.com.demaenergy.db;

import com.typesafe.config.Config;
import com.typesafe.config.ConfigFactory;
import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;

import java.sql.Connection;
import java.sql.SQLException;

public class DBFactory {
    private static final HikariDataSource ds;

    static {
        Config config = ConfigFactory.load();
        final HikariConfig hikariConfig = new HikariConfig();
        hikariConfig.setJdbcUrl(config.getString("datasource.url"));
        hikariConfig.setUsername(config.getString("datasource.username"));
        hikariConfig.setPassword(config.getString("datasource.password"));
        hikariConfig.setMaximumPoolSize(config.getInt("datasource.poolSize"));
        hikariConfig.setConnectionTimeout(config.getInt("datasource.connectionTimeout"));
        hikariConfig.validate();
        ds = new HikariDataSource(hikariConfig);
    }

    private DBFactory() {
    }

    public static Connection getConnection() {
        try {
            return ds.getConnection();
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
    }


}