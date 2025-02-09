from typing import Dict, Any
from datetime import datetime
from .base_simulator import BaseSimulator
from ..Load.data_center_cooling import DataCenterCooling
import numpy as np

class DataCenterCoolingSimulator(BaseSimulator):
    """Simulator for data center cooling systems"""
    
    def __init__(self, model: DataCenterCooling, config: Dict[str, Any]):
        super().__init__(model, config)
        self.heat_exchanger_model = config.get('heat_exchanger_model', 'detailed')
        self.ambient_data = config.get('ambient_data', [])
        
    def step(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ambient_temp = inputs.get('ambient_temperature', 25.0)
        thermal_load = inputs.get('thermal_load', 0.0)
        
        # Update flow rates based on thermal load
        oil_flow = min(thermal_load / 1000, self.model.capacity/100)
        water_flow = oil_flow * 1.2  # Slightly higher water flow for better heat transfer
        self.model.update_flow_rates(oil_flow, water_flow)
        
        # Calculate heat exchanger performance
        if self.heat_exchanger_model == 'detailed':
            self._simulate_heat_exchanger(ambient_temp)
            
        # Calculate power consumption
        power = self.model.calculate_power_consumption(ambient_temp)
        
        # Get current state
        state = self.model.get_status()
        self.save_state(state)
        
        return state
        
    def _simulate_heat_exchanger(self, ambient_temp: float):
        """Detailed heat exchanger simulation"""
        # Calculate temperature changes
        oil_temp_change = (self.model.oil_flow_rate * 
                          self.model.oil_properties['specific_heat'] * 
                          self.model.heat_exchanger_effectiveness)
        
        water_temp_change = (self.model.water_flow_rate * 
                           self.model.water_properties['specific_heat'] * 
                           self.model.heat_exchanger_effectiveness)
        
        # Update temperatures
        new_oil_temp = self.model.oil_temperature - oil_temp_change/1000
        new_water_temp = self.model.water_temperature + water_temp_change/1000
        
        self.model.update_temperatures(new_oil_temp, new_water_temp) 