
```python
cost_per_btu_dict = {
    "GasTurbinesPlants": 1.25,
    "GasCombinedCyclePlants": 1.25,
    "CrudeOilCombinedCyclePlants": 13.79,
    "HFOCombinedCyclePlants": 8.90,
    "CrudeOilPoweredSteamTurbines": 13.79,   
    "HFOPoweredSteamTurbines": 8.90,
    "DieselGenerators": 8.38,
    "DieselPoweredSteamTurbines": 8.38,
    "SolarPV": 0.0,
    "WindFarm": 0.0
}
```

---

# Cost per MMBTU Calculations in Saudi Arabia

## Overview

This document outlines the assumptions and calculations used to determine the cost per MMBTU for various fuel types in Saudi Arabia, incorporating the latest diesel price of 1.15 SAR per liter and a crude oil price of $80 per barrel as of September 2024.

## General Assumptions

- **Currency**: All prices are in USD.
- **Exchange Rate**: 1 Saudi Riyal (SAR) ≈ 0.2667 USD.
- **Energy Content**: Standard energy content values are used for each fuel type.
- **Subsidies**: Prices reflect the domestic market in Saudi Arabia, accounting for any government subsidies where applicable.

## Fuel Types and Calculations

### 1. Natural Gas

- **Used in**: Gas Turbine Plants, Gas Combined Cycle Plants.
- **Local Price**: $1.25 per MMBTU (regulated price by the Saudi government).
- **Calculation**:
  - **Cost per MMBTU**: **$1.25**

### 2. Crude Oil

- **Used in**: Crude Oil Combined Cycle Plants, Crude Oil Powered Steam Turbines.
- **Local Price**: $80 per barrel (updated price).
- **Energy Content**: 5.8 MMBTU per barrel.
- **Calculation**:
  - **Cost per MMBTU**: $80 ÷ 5.8 MMBTU/barrel ≈ **$13.79**

### 3. Heavy Fuel Oil (HFO)

- **Used in**: HFO Combined Cycle Plants, HFO Powered Steam Turbines.
- **Assumed Price**: HFO is typically priced at approximately 70% of crude oil.
  - **HFO Price per Barrel**: $80 × 0.7 = **$56**
- **Energy Content**: 6.287 MMBTU per barrel.
- **Calculation**:
  - **Cost per MMBTU**: $56 ÷ 6.287 MMBTU/barrel ≈ **$8.90**

### 4. Diesel Fuel

- **Used in**: Diesel Generators, Diesel Powered Steam Turbines.
- **Local Price**: 1.15 SAR per liter.
- **Exchange Rate**: 1 SAR ≈ 0.2667 USD.
- **Price in USD per Liter**:
  - $0.2667 × 1.15 SAR/liter ≈ **$0.3067** per liter.
- **Conversion Factors**:
  - 1 US gallon = 3.78541 liters.
  - **Price per Gallon**:
    - $0.3067 × 3.78541 ≈ **$1.16** per gallon.
  - Energy Content: 138,500 BTU per gallon.
- **Calculation**:
  - **Gallons per MMBTU**:
    - 1,000,000 BTU ÷ 138,500 BTU/gallon ≈ **7.22** gallons.
  - **Cost per MMBTU**:
    - 7.22 gallons × $1.16/gallon ≈ **$8.38**

### 5. Solar PV and Wind Farms

- **Fuel Cost**: **$0.00 per MMBTU** (no fuel required).

## Summary Table

| Fuel Type                          | Cost per MMBTU (USD) |
|------------------------------------|----------------------|
| **Natural Gas**                    | **$1.25**            |
| **Crude Oil**                      | **$13.79**           |
| **Heavy Fuel Oil (HFO)**           | **$8.90**            |
| **Diesel Fuel**                    | **$8.38**            |
| **Solar PV**                       | **$0.00**            |
| **Wind Farm**                      | **$0.00**            |

## Detailed Calculations and Assumptions

### Natural Gas

- **Price Stability**: The regulated price of $1.25 per MMBTU is assumed to remain stable due to government policies.
- **Reference**: Saudi Aramco reports and industry publications.

### Crude Oil

- **Updated Price**: $80 per barrel as per the latest market update.
- **Energy Content**: Standard value of 5.8 MMBTU per barrel.
- **Calculation**:
  - Cost per MMBTU = $80 ÷ 5.8 ≈ $13.79.
- **Assumptions**:
  - No subsidies are applied to this price.

### Heavy Fuel Oil (HFO)

- **Price Relation to Crude Oil**: Assumed to be 70% of crude oil price.
- **Calculation**:
  - HFO Price per Barrel = $80 × 0.7 = $56.
  - Cost per MMBTU = $56 ÷ 6.287 ≈ $8.90.
- **Energy Content**: 6.287 MMBTU per barrel (standard value).
- **Assumptions**:
  - The 70% factor reflects typical market conditions for HFO relative to crude oil.

### Diesel Fuel

- **Updated Local Price**: 1.15 SAR per liter.
- **Price in USD**:
  - $0.2667 × 1.15 = $0.3067 per liter.
- **Price per Gallon**:
  - $0.3067 × 3.78541 = $1.16 per gallon.
- **Energy Content**:
  - 138,500 BTU per gallon.
- **Calculation**:
  - Gallons per MMBTU = 1,000,000 BTU ÷ 138,500 BTU/gallon ≈ 7.22 gallons.
  - Cost per MMBTU = 7.22 gallons × $1.16/gallon ≈ $8.38.
- **Assumptions**:
  - Exchange rate remains constant.
  - No additional taxes or subsidies are applied.

### Solar PV and Wind Farms

- **Fuel Cost**: Zero, as these sources do not require fuel.
- **Assumptions**:
  - Operational and maintenance costs are not included in the fuel cost per MMBTU.

## Notes and References

- **Exchange Rate**:
  - Based on the average exchange rate: 1 SAR ≈ 0.2667 USD.
  - *Reference*: Saudi Central Bank exchange rates as of September 2024.

- **Fuel Prices**:
  - Diesel price: *GlobalPetrolPrices.com* and *Global Econ Data*.
  - Crude oil price: International market price as of September 2024.

- **Energy Content Values**:
  - Derived from standard fuel property databases and the U.S. Energy Information Administration (EIA).

- **Market Conditions**:
  - Prices reflect the domestic market in Saudi Arabia and may differ from global averages due to subsidies or taxes.

- **Subsidies**:
  - For this calculation, subsidies are not applied unless specified by the updated prices provided.

## Conclusion

The updated cost per MMBTU for various fuels in Saudi Arabia has been calculated using the latest diesel price of 1.15 SAR per liter and a crude oil price of $80 per barrel. These figures provide a current snapshot of fuel costs for power generation in the region.

