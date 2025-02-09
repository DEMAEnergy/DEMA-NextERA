package sa.com.demaenergy.mining.loadoptimizer.http.model;

public record msMachineData(String macAddress, float hashRate, float presetConsumption, float consumption, int phase,
                          boolean prevState, boolean desiredState) {
}
