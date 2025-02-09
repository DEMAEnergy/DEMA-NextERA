package sa.com.demaenergy.energymonitor.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
@JsonIgnoreProperties(ignoreUnknown = true)
public record EmergencyEventResponse(@JsonProperty("statusCode") String statusCode,
                                     @JsonProperty("statusMessage") String statusMessage,
                                     @JsonProperty("result") EmergencyEvent emergencyEvent) {
    @JsonIgnoreProperties(ignoreUnknown = true)
    public record EmergencyEvent(@JsonProperty("ACTIVE") int active,
                                 @JsonProperty("COMMAND") String command) {
    }
}