package sa.com.demaenergy.energymonitor.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.math.BigDecimal;
import java.util.List;
@JsonIgnoreProperties(ignoreUnknown = true)
public record EnergyPriceResponse(@JsonProperty("statusCode") String statusCode,
                                  @JsonProperty("statusMessage") String statusMessage,
                                  @JsonProperty("result") List<EnergyPrice> energyPrice) {
    @JsonIgnoreProperties(ignoreUnknown = true)
    public record EnergyPrice(@JsonProperty("INTERVALFORMATED") String intervalFormated,
                              @JsonProperty("INTERVAL") String interval,
                              @JsonProperty("LMP") BigDecimal price) {
    }
}
