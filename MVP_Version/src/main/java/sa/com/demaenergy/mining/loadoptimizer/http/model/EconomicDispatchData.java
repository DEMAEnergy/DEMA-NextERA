package sa.com.demaenergy.mining.loadoptimizer.http.model;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public record EconomicDispatchData(

        @JsonProperty("energy_price") double energy_price,
        @JsonProperty("strike_price") List<Double> strike_price,
        @JsonProperty("consumption_per_machine") List<Double> consumptionPerMachine) {

}

