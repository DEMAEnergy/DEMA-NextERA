package sa.com.demaenergy.mining.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
@JsonIgnoreProperties(ignoreUnknown = true)
public record TokenRequest(@JsonProperty("token") String token) {
}
