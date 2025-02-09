from typing import Dict, Any
from .base_source import BaseSource
import math

class PVSystem(BaseSource):
    """Model for Photovoltaic Systems"""
    
    def __init__(self, resource_id: str, capacity: float, location: Dict[str, float],
                 efficiency: float = 0.2,
                 temperature_coefficient: float = -0.004,  # Power reduction per degree C
                 inverter_efficiency: float = 0.96):
        super().__init__(resource_id, capacity, location)
        self.efficiency = efficiency
        self.temperature_coefficient = temperature_coefficient
        self.inverter_efficiency = inverter_efficiency
        self.panel_temperature = 25.0  # Standard Test Conditions temperature
        self.irradiance = 0.0  # Current solar irradiance (W/m2)
        
    def start(self) -> bool:
        if self.status == "idle":
            self.status = "running"
            return True
        return False
        
    def stop(self) -> bool:
        if self.status == "running":
            self.status = "idle"
            self.current_power = 0.0
            return True
        return False
    
    def get_status(self) -> Dict[str, Any]:
        status = super().get_status()
        status.update({
            "panel_temperature": self.panel_temperature,
            "irradiance": self.irradiance,
            "efficiency": self.efficiency * self.inverter_efficiency
        })
        return status
    
    def calculate_power_output(self, irradiance: float, ambient_temp: float) -> float:
        """Calculate power output based on environmental conditions"""
        self.irradiance = irradiance
        # Simplified panel temperature model
        self.panel_temperature = ambient_temp + (irradiance / 800) * 30
        
        # Temperature effect on efficiency
        temp_effect = 1 + self.temperature_coefficient * (self.panel_temperature - 25)
        
        # Calculate power output
        theoretical_output = (self.capacity * irradiance / 1000) * temp_effect
        self.current_power = min(self.capacity, 
                               theoretical_output * self.efficiency * self.inverter_efficiency)
        return self.current_power 