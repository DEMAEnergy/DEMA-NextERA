package sa.com.demaenergy.mining.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public record MinerSummaryRequest(@JsonProperty("miner") MinerSummary minerSummary) {
    @JsonIgnoreProperties(ignoreUnknown = true)
    public record MinerSummary(@JsonProperty("miner_status") MinerStatus minerStatus,
                               @JsonProperty("miner_type") String minerType,
                               @JsonProperty("average_hashrate") double averageHashRate,
                               @JsonProperty("instant_hashrate") double instantHashRate,
                               @JsonProperty("hr_realtime") double hrRealTime,
                               @JsonProperty("hr_average") double hrAverage,
                               @JsonProperty("power_consumption") int powerConsumption,
                               @JsonProperty("power_usage") int powerUsage,
                               @JsonProperty("power_efficiency") double powerEfficiency,
                               @JsonProperty("chip_temp") ChipTemp chipTemp,
                               @JsonProperty("pcb_temp") PcbTemp pcbTemp
                               ) {
        public record PcbTemp(@JsonProperty("min") int min,
                              @JsonProperty("max") int max) {
        }

        public record ChipTemp(@JsonProperty("min") int min,
                               @JsonProperty("max") int max) {
        }

        @JsonIgnoreProperties(ignoreUnknown = true)
        public record MinerStatus(@JsonProperty("miner_state") String minerState,
                                  @JsonProperty("miner_state_time") int minerStateTime) {
        }

    }
}

//{
//	"miner": {
//		"miner_status": {
//			"miner_state": "initializing",
//			"miner_state_time": 21
//		},
//		"miner_type": "Antminer S19j Pro (Vnish 1.2.0-rc5)",
//		"average_hashrate": 0.0,
//		"instant_hashrate": 0.0,
//		"hr_realtime": 0.0,
//		"hr_average": 0.0,
//		"pcb_temp": {
//			"min": 22,
//			"max": 30
//		},
//		"chip_temp": {
//			"min": 37,
//			"max": 45
//		},
//		"power_consumption": 146,
//		"power_usage": 146,
//		"power_efficiency": 0.0,
//		"hw_errors_percent": 0.0,
//		"hr_error": 0.0,
//		"hw_errors": 0,
//		"devfee_percent": 0.0,
//		"devfee": 0.0,
//		"pools": [
//			{
//				"id": 0,
//				"url": "btc.global.luxor.tech:700",
//				"pool_type": "UserPool",
//				"user": "*****",
//				"status": "active",
//				"asic_boost": true,
//				"diff": "131K",
//				"accepted": 0,
//				"rejected": 0,
//				"stale": 0,
//				"ls_diff": 0.0,
//				"ls_time": "0",
//				"diffa": 0.0,
//				"ping": 0
//			},
//			{
//				"id": 1,
//				"url": "stratum.braiins.com:3333",
//				"pool_type": "UserPool",
//				"user": "*****",
//				"status": "working",
//				"asic_boost": true,
//				"diff": "8.19K",
//				"accepted": 0,
//				"rejected": 0,
//				"stale": 0,
//				"ls_diff": 0.0,
//				"ls_time": "0",
//				"diffa": 0.0,
//				"ping": 0
//			},
//			{
//				"id": 2,
//				"url": "stratum.braiins.com:3333",
//				"pool_type": "UserPool",
//				"user": "*****",
//				"status": "active",
//				"asic_boost": true,
//				"diff": "8.19K",
//				"accepted": 0,
//				"rejected": 0,
//				"stale": 0,
//				"ls_diff": 0.0,
//				"ls_time": "0",
//				"diffa": 0.0,
//				"ping": 0
//			},
//			{
//				"id": 3,
//				"url": "DevFee",
//				"pool_type": "DevFee",
//				"user": "*****",
//				"status": "working",
//				"asic_boost": true,
//				"diff": "2.05K",
//				"accepted": 0,
//				"rejected": 0,
//				"stale": 0,
//				"ls_diff": 0.0,
//				"ls_time": "0",
//				"diffa": 0.0,
//				"ping": 0
//			},
//			{
//				"id": 4,
//				"url": "DevFee",
//				"pool_type": "DevFee",
//				"user": "*****",
//				"status": "working",
//				"asic_boost": true,
//				"diff": "2.05K",
//				"accepted": 0,
//				"rejected": 0,
//				"stale": 0,
//				"ls_diff": 0.0,
//				"ls_time": "0",
//				"diffa": 0.0,
//				"ping": 0
//			}
//		],
//		"cooling": {
//			"fan_num": 4,
//			"fans": [
//				{
//					"id": 0,
//					"rpm": 0,
//					"status": "lost"
//				},
//				{
//					"id": 1,
//					"rpm": 0,
//					"status": "lost"
//				},
//				{
//					"id": 2,
//					"rpm": 0,
//					"status": "lost"
//				},
//				{
//					"id": 3,
//					"rpm": 0,
//					"status": "lost"
//				}
//			],
//			"settings": {
//				"mode": {
//					"name": "immersion"
//				}
//			},
//			"fan_duty": 100
//		},
//		"chains": [
//			{
//				"id": 1,
//				"frequency": 0.0,
//				"voltage": 15000,
//				"power_consumption": 50,
//				"hashrate_ideal": 0.0,
//				"hashrate_rt": 0.0,
//				"hashrate_percentage": 0.0,
//				"hr_error": 0.0,
//				"hw_errors": 0,
//				"pcb_temp": {
//					"min": 23,
//					"max": 30
//				},
//				"chip_temp": {
//					"min": 38,
//					"max": 45
//				},
//				"chip_statuses": {
//					"red": 126,
//					"orange": 0,
//					"grey": 0
//				},
//				"status": {
//					"state": "initializing"
//				}
//			},
//			{
//				"id": 2,
//				"frequency": 0.0,
//				"voltage": 15000,
//				"power_consumption": 47,
//				"hashrate_ideal": 0.0,
//				"hashrate_rt": 0.0,
//				"hashrate_percentage": 0.0,
//				"hr_error": 0.0,
//				"hw_errors": 0,
//				"pcb_temp": {
//					"min": 22,
//					"max": 29
//				},
//				"chip_temp": {
//					"min": 37,
//					"max": 44
//				},
//				"chip_statuses": {
//					"red": 126,
//					"orange": 0,
//					"grey": 0
//				},
//				"status": {
//					"state": "initializing"
//				}
//			},
//			{
//				"id": 3,
//				"frequency": 0.0,
//				"voltage": 15000,
//				"power_consumption": 49,
//				"hashrate_ideal": 0.0,
//				"hashrate_rt": 0.0,
//				"hashrate_percentage": 0.0,
//				"hr_error": 0.0,
//				"hw_errors": 0,
//				"pcb_temp": {
//					"min": 22,
//					"max": 30
//				},
//				"chip_temp": {
//					"min": 37,
//					"max": 45
//				},
//				"chip_statuses": {
//					"red": 126,
//					"orange": 0,
//					"grey": 0
//				},
//				"status": {
//					"state": "initializing"
//				}
//			}
//		],
//		"found_blocks": 0,
//		"best_share": 0
//	}
//}