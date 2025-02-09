from typing import Dict, Any
from datetime import datetime
from .hvac import HVAC
import numpy as np
from scipy.interpolate import CubicSpline

class DataCenterCooling(HVAC):
    """Model for Data Center Cooling Systems with detailed thermal simulation"""
    
    def __init__(self, resource_id: str, capacity: float, location: Dict[str, float],
                 temperature_setpoint: float = 22.0,
                 temperature_deadband: float = 1.0,
                 cop: float = 3.5):
        super().__init__(resource_id, capacity, location, temperature_setpoint, 
                        temperature_deadband, cop)
        
        # Initialize cooling system components
        self.oil_properties = {
            'density': 850,
            'specific_heat': 2000,
            'viscosity': 0.065,
        }
        self.water_properties = {
            'density': 997,
            'specific_heat': 4182,
            'viscosity': 0.001,
        }
        
        # Component states
        self.oil_temperature = temperature_setpoint
        self.water_temperature = temperature_setpoint
        self.oil_flow_rate = 0.0
        self.water_flow_rate = 0.0
        self.heat_exchanger_effectiveness = 0.85
        
    def get_status(self) -> Dict[str, Any]:
        status = super().get_status()
        status.update({
            "oil_temperature": self.oil_temperature,
            "water_temperature": self.water_temperature,
            "oil_flow_rate": self.oil_flow_rate,
            "water_flow_rate": self.water_flow_rate,
            "heat_exchanger_effectiveness": self.heat_exchanger_effectiveness
        })
        return status
        
    def calculate_power_consumption(self, ambient_temperature: float) -> float:
        """Calculate power consumption with detailed cooling system model"""
        # Calculate required cooling load
        delta_t = abs(ambient_temperature - self.temperature_setpoint)
        cooling_load = self.capacity * (delta_t / 10)  # Simplified load calculation
        
        # Calculate pump power consumption
        pump_power = (self.oil_flow_rate * 0.1) + (self.water_flow_rate * 0.1)  # Simplified pump power
        
        # Calculate heat exchanger performance
        q_max = min(
            self.oil_flow_rate * self.oil_properties['specific_heat'],
            self.water_flow_rate * self.water_properties['specific_heat']
        ) * (self.oil_temperature - self.water_temperature)
        
        heat_transfer = self.heat_exchanger_effectiveness * q_max
        
        # Calculate total power consumption
        total_power = pump_power + (heat_transfer / self.cop)
        
        return min(self.capacity, total_power)
    
    def update_flow_rates(self, oil_flow: float, water_flow: float) -> bool:
        """Update system flow rates"""
        if 0 <= oil_flow <= self.capacity/100 and 0 <= water_flow <= self.capacity/100:
            self.oil_flow_rate = oil_flow
            self.water_flow_rate = water_flow
            return True
        return False
    
    def update_temperatures(self, oil_temp: float, water_temp: float) -> bool:
        """Update system temperatures"""
        if 0 <= oil_temp <= 100 and 0 <= water_temp <= 100:
            self.oil_temperature = oil_temp
            self.water_temperature = water_temp
            return True
        return False 