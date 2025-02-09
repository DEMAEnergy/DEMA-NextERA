from typing import Dict, Any
from .base_load import BaseLoad

class Motor(BaseLoad):
    """Model for electric motors"""
    
    def __init__(self, resource_id: str, capacity: float, location: Dict[str, float],
                 efficiency: float = 0.9, 
                 rated_speed: float = 1750.0,  # RPM
                 min_speed: float = 0.0):
        super().__init__(resource_id, capacity, location)
        self.efficiency = efficiency
        self.rated_speed = rated_speed
        self.min_speed = min_speed
        self.current_speed = 0.0
        self.load_factor = 1.0
        
    def start(self) -> bool:
        if self.status == "idle":
            self.status = "running"
            self.current_speed = self.rated_speed
            return True
        return False
        
    def stop(self) -> bool:
        if self.status == "running":
            self.status = "idle"
            self.current_speed = 0.0
            self.current_power = 0.0
            return True
        return False
    
    def get_status(self) -> Dict[str, Any]:
        status = super().get_status()
        status.update({
            "current_speed": self.current_speed,
            "efficiency": self.efficiency,
            "load_factor": self.load_factor
        })
        return status
    
    def set_speed(self, speed: float) -> bool:
        """Update motor speed"""
        if self.min_speed <= speed <= self.rated_speed:
            self.current_speed = speed
            # Update power based on speed (simplified cubic relationship for fans/pumps)
            speed_ratio = speed / self.rated_speed
            self.current_power = self.capacity * (speed_ratio ** 3) * self.load_factor
            return True
        return False
    
    def set_load_factor(self, load_factor: float) -> bool:
        """Update load factor (0-1)"""
        if 0 <= load_factor <= 1:
            self.load_factor = load_factor
            return True
        return False 