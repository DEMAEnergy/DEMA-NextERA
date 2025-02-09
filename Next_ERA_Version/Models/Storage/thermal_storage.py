from typing import Dict, Any
from .base_storage import BaseStorage
from datetime import datetime

class ThermalStorage(BaseStorage):
    """Model for Thermal Energy Storage Systems"""
    
    def __init__(self, resource_id: str, capacity: float, location: Dict[str, float],
                 max_charge_rate: float, max_discharge_rate: float,
                 storage_type: str = "water",
                 max_temperature: float = 95.0,  # Celsius
                 min_temperature: float = 5.0):  # Celsius
        super().__init__(resource_id, capacity, location, max_charge_rate, max_discharge_rate)
        self.storage_type = storage_type
        self.max_temperature = max_temperature
        self.min_temperature = min_temperature
        self.current_temperature = min_temperature
        self.ambient_temperature = 20.0
        self.heat_loss_coefficient = 0.1  # kW/°C
        
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
            "storage_type": self.storage_type,
            "current_temperature": self.current_temperature,
            "ambient_temperature": self.ambient_temperature,
            "thermal_losses": self.calculate_thermal_losses()
        })
        return status
    
    def charge(self, power: float, duration: float) -> bool:
        """Charge (heat) the thermal storage"""
        if power > self.max_charge_rate:
            return False
            
        # Calculate temperature rise
        energy = power * duration * self.round_trip_efficiency
        temp_rise = self.calculate_temperature_change(energy)
        new_temp = self.current_temperature + temp_rise
        
        if new_temp <= self.max_temperature:
            self.current_temperature = new_temp
            self.current_power = power
            self.state_of_charge = self.calculate_state_of_charge()
            self.last_updated = datetime.now()
            return True
        return False
    
    def discharge(self, power: float, duration: float) -> bool:
        """Discharge (cool) the thermal storage"""
        if power > self.max_discharge_rate:
            return False
            
        # Calculate temperature drop
        energy = power * duration
        temp_drop = self.calculate_temperature_change(energy)
        new_temp = self.current_temperature - temp_drop
        
        if new_temp >= self.min_temperature:
            self.current_temperature = new_temp
            self.current_power = -power
            self.state_of_charge = self.calculate_state_of_charge()
            self.last_updated = datetime.now()
            return True
        return False
    
    def calculate_thermal_losses(self) -> float:
        """Calculate thermal losses to ambient"""
        temperature_difference = self.current_temperature - self.ambient_temperature
        return self.heat_loss_coefficient * temperature_difference
    
    def calculate_temperature_change(self, energy: float) -> float:
        """Calculate temperature change for given energy"""
        # Simplified calculation using water's specific heat capacity
        if self.storage_type == "water":
            specific_heat = 4.186  # kJ/kg°C
            mass = self.capacity * 3600 / (specific_heat * (self.max_temperature - self.min_temperature))
            return energy * 3600 / (mass * specific_heat)
        return 0.0
    
    def calculate_state_of_charge(self) -> float:
        """Calculate state of charge based on temperature"""
        temp_range = self.max_temperature - self.min_temperature
        current_range = self.current_temperature - self.min_temperature
        return (current_range / temp_range) * 100 