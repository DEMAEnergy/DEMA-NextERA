package sa.com.demaenergy.energymonitor.model;

public record PredictedPrices(java.sql.Timestamp rtd_datetime, float price, float price_5, float price_10,
                              float price_15, float price_20, float price_25, float price_30,
                              float price_35, float price_40, float price_45, float price_50,
                              float price_55) {
}