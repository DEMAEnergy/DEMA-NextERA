package sa.com.demaenergy.mining.loadoptimizer.http.model;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public record msRequestResponseData(
        @JsonProperty("id") String id,
        @JsonProperty("status") String status,
        @JsonProperty("machine_data") List<MachineSelectionData> machineData) {
}

