package sa.com.demaenergy.mining.loadoptimizer.http.model;

import com.fasterxml.jackson.annotation.JsonProperty;

public record edRequestResponseData(
        @JsonProperty("id") String id,
        @JsonProperty("status") String status,
        @JsonProperty("target_power") String targetPower) {
}

