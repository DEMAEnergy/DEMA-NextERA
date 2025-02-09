from typing import Dict, Any
from ..base_model import BaseModel
from datetime import datetime

class BaseStorage(BaseModel):
    """Base class for all energy storage resources"""
    
    def __init__(self, resource_id: str, capacity: float, location: Dict[str, float],
                 max_charge_rate: float, max_discharge_rate: float,
                 round_trip_efficiency: float = 0.85):
        super().__init__(resource_id, capacity, location)
        self.max_charge_rate = max_charge_rate
        self.max_discharge_rate = max_discharge_rate
        self.round_trip_efficiency = round_trip_efficiency
        self.state_of_charge = 0.0  # percentage
        self.current_power = 0.0  # positive for charging, negative for discharging
        
    def get_status(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "status": self.status,
            "current_power": self.current_power,
            "state_of_charge": self.state_of_charge,
            "last_updated": self.last_updated
        }
    
    def update_setpoint(self, value: float) -> bool:
        # Check if charging or discharging
        if value > 0:  # Charging
            if value <= self.max_charge_rate and self.state_of_charge < 100:
                self.current_power = value
                self.last_updated = datetime.now()
                return True
        else:  # Discharging
            if abs(value) <= self.max_discharge_rate and self.state_of_charge > 0:
                self.current_power = value
                self.last_updated = datetime.now()
                return True
        return False
    
    def calculate_available_capacity(self) -> float:
        """Calculate available capacity for charging/discharging"""
        return self.capacity * (100 - self.state_of_charge) / 100 