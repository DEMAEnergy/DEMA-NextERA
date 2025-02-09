from typing import Dict, Any
from .base_source import BaseSource
import math

class WindTurbine(BaseSource):
    """Model for Wind Turbines"""
    
    def __init__(self, resource_id: str, capacity: float, location: Dict[str, float],
                 cut_in_speed: float = 3.0,  # m/s
                 cut_out_speed: float = 25.0,  # m/s
                 rated_wind_speed: float = 12.0,  # m/s
                 hub_height: float = 80.0):  # meters
        super().__init__(resource_id, capacity, location)
        self.cut_in_speed = cut_in_speed
        self.cut_out_speed = cut_out_speed
        self.rated_wind_speed = rated_wind_speed
        self.hub_height = hub_height
        self.current_wind_speed = 0.0
        
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
            "current_wind_speed": self.current_wind_speed,
            "hub_height": self.hub_height
        })
        return status
    
    def calculate_power_output(self, wind_speed: float, air_density: float = 1.225) -> float:
        """Calculate power output based on wind conditions"""
        self.current_wind_speed = wind_speed
        
        if wind_speed < self.cut_in_speed or wind_speed > self.cut_out_speed:
            self.current_power = 0.0
            return 0.0
            
        if wind_speed >= self.rated_wind_speed:
            self.current_power = self.capacity
            return self.capacity
            
        # Power curve approximation (cubic relationship)
        wind_ratio = (wind_speed - self.cut_in_speed) / (self.rated_wind_speed - self.cut_in_speed)
        theoretical_power = self.capacity * (wind_ratio ** 3)
        
        # Apply air density correction
        density_correction = air_density / 1.225  # Standard air density correction
        self.current_power = theoretical_power * density_correction
        
        return self.current_power
    
    def adjust_wind_speed_for_height(self, reference_speed: float, reference_height: float,
                                   roughness_length: float = 0.1) -> float:
        """Adjust wind speed for hub height using log law"""
        return reference_speed * (math.log(self.hub_height / roughness_length) / 
                                math.log(reference_height / roughness_length)) 