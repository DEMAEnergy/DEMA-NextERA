from typing import Dict, Any
from ..base_model import BaseModel
from datetime import datetime

class BaseSource(BaseModel):
    """Base class for all power source resources"""
    
    def __init__(self, resource_id: str, capacity: float, location: Dict[str, float],
                 min_power: float = 0.0, ramp_rate: float = 1.0):
        super().__init__(resource_id, capacity, location)
        self.min_power = min_power
        self.ramp_rate = ramp_rate  # Power change per minute (kW/min)
        self.current_power = 0.0
        self.fuel_level = 100.0  # Applicable for generators, always 100 for renewables
        
    def get_status(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "status": self.status,
            "current_power": self.current_power,
            "fuel_level": self.fuel_level,
            "last_updated": self.last_updated
        }
    
    def update_setpoint(self, value: float) -> bool:
        if self.min_power <= value <= self.capacity:
            # Check if requested change is within ramp rate
            power_change = abs(value - self.current_power)
            if power_change <= self.ramp_rate:
                self.current_power = value
                self.last_updated = datetime.now()
                return True
        return False 