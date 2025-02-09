package sa.com.demaenergy.energymonitor.model;

import java.sql.Timestamp;

public record Dam(String id, String bidId, Timestamp startTime, Timestamp endTime, String settlementPoint, float awardedMwh, float spp, Timestamp createdAt) {
}