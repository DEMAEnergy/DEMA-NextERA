package sa.com.demaenergy.mining.loadoptimizer.http.model;

import com.fasterxml.jackson.annotation.JsonProperty;

public record ResponseData(
        @JsonProperty("id") String requestID
) {
}
