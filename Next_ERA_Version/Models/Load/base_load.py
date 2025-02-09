from typing import Dict, Any
from ..base_model import BaseModel
from datetime import datetime

class BaseLoad(BaseModel):
    """Base class for all load resources"""
    
    def __init__(self, resource_id: str, capacity: float, location: Dict[str, float], 
                 min_power: float = 0.0, power_factor: float = 0.95):
        super().__init__(resource_id, capacity, location)
        self.min_power = min_power
        self.power_factor = power_factor
        self.current_power = 0.0
        
    def get_status(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "status": self.status,
            "current_power": self.current_power,
            "power_factor": self.power_factor,
            "last_updated": self.last_updated
        }
    
    def update_setpoint(self, value: float) -> bool:
        if self.min_power <= value <= self.capacity:
            self.current_power = value
            self.last_updated = datetime.now()
            return True
        return False 