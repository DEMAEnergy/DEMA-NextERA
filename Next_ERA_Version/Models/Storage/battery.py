from typing import Dict, Any
from .base_storage import BaseStorage
from datetime import datetime

class Battery(BaseStorage):
    """Model for Battery Energy Storage Systems"""
    
    def __init__(self, resource_id: str, capacity: float, location: Dict[str, float],
                 max_charge_rate: float, max_discharge_rate: float,
                 chemistry: str = "Li-ion",
                 depth_of_discharge: float = 0.8,
                 cycle_life: int = 5000):
        super().__init__(resource_id, capacity, location, max_charge_rate, max_discharge_rate)
        self.chemistry = chemistry
        self.depth_of_discharge = depth_of_discharge
        self.cycle_life = cycle_life
        self.cycles_used = 0
        self.temperature = 25.0  # Celsius
        
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
            "chemistry": self.chemistry,
            "temperature": self.temperature,
            "cycles_used": self.cycles_used,
            "remaining_cycles": self.cycle_life - self.cycles_used,
            "available_capacity": self.calculate_available_capacity()
        })
        return status
    
    def charge(self, power: float, duration: float) -> bool:
        """Charge the battery with specified power for given duration (hours)"""
        if power > self.max_charge_rate:
            return False
            
        energy = power * duration * self.round_trip_efficiency
        new_soc = self.state_of_charge + (energy / self.capacity) * 100
        
        if new_soc <= 100:
            self.state_of_charge = new_soc
            self.current_power = power
            self.last_updated = datetime.now()
            return True
        return False
    
    def discharge(self, power: float, duration: float) -> bool:
        """Discharge the battery with specified power for given duration (hours)"""
        if power > self.max_discharge_rate:
            return False
            
        energy = power * duration
        new_soc = self.state_of_charge - (energy / self.capacity) * 100
        
        if new_soc >= (100 - self.depth_of_discharge * 100):
            self.state_of_charge = new_soc
            self.current_power = -power  # Negative for discharge
            self.cycles_used += duration / 24  # Approximate cycle counting
            self.last_updated = datetime.now()
            return True
        return False
    
    def set_temperature(self, temperature: float) -> bool:
        """Update battery temperature and adjust performance"""
        self.temperature = temperature
        # Simplified temperature derating
        if temperature < 0 or temperature > 40:
            self.max_charge_rate *= 0.8
            self.max_discharge_rate *= 0.8
        return True 