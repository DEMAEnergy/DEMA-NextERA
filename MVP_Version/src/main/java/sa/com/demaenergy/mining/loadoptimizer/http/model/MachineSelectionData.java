package sa.com.demaenergy.mining.loadoptimizer.http.model;

import com.fasterxml.jackson.annotation.JsonProperty;

public record MachineSelectionData(
        @JsonProperty("mac_address") String macAddress,
        @JsonProperty("hash_rate") float hashRate,
        @JsonProperty("preset_consumption") float presetConsumption,
        @JsonProperty("consumption") float consumption,
        @JsonProperty("prev_state") boolean previousState,
        @JsonProperty("phase") int phase,
        @JsonProperty("desired_state") boolean desiredState)  {
}