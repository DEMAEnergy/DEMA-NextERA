from typing import Dict, Any
from .base_load import BaseLoad

class HVAC(BaseLoad):
    """Model for HVAC systems"""
    
    def __init__(self, resource_id: str, capacity: float, location: Dict[str, float],
                 temperature_setpoint: float = 22.0, 
                 temperature_deadband: float = 1.0,
                 cop: float = 3.5):  # Coefficient of Performance
        super().__init__(resource_id, capacity, location)
        self.temperature_setpoint = temperature_setpoint
        self.temperature_deadband = temperature_deadband
        self.cop = cop
        self.current_temperature = temperature_setpoint
        self.mode = "cooling"  # cooling or heating
        
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
            "temperature_setpoint": self.temperature_setpoint,
            "current_temperature": self.current_temperature,
            "mode": self.mode,
            "cop": self.cop
        })
        return status
    
    def set_temperature(self, temperature: float) -> bool:
        """Update temperature setpoint"""
        self.temperature_setpoint = temperature
        return True
    
    def calculate_power_consumption(self, ambient_temperature: float) -> float:
        """Calculate power consumption based on temperature difference"""
        delta_t = abs(ambient_temperature - self.temperature_setpoint)
        return min(self.capacity, (delta_t * self.capacity) / (self.cop * 10))  # Simplified model 