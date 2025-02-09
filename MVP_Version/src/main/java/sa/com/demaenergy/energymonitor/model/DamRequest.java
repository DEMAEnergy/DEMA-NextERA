package sa.com.demaenergy.energymonitor.model;

import com.fasterxml.jackson.annotation.JsonProperty;


import java.util.List;

public record DamRequest(@JsonProperty("dam") List<damPurchase> damPurchase) {
    public record damPurchase(@JsonProperty("Trading Date") String tradingDate, @JsonProperty("BID ID") String bidID,
                              @JsonProperty("Start Time") String startTime, @JsonProperty("End Time") String endTime,
                              @JsonProperty("Settlement Point") String settlementPoint,
                              @JsonProperty("Awarded MWh") float awardedMwh, @JsonProperty("SPP") float spp) {
    }
}
