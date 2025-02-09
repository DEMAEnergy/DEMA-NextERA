from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

@dataclass
class SimulationConfig:
    start_time: datetime
    end_time: datetime
    time_step: int  # in seconds
    components: Dict[str, 'ComponentConfig']

@dataclass
class ComponentConfig:
    type: str  # e.g., "battery", "solar", "wind"
    capacity: float
    efficiency: float
    initial_state: float
    constraints: Dict[str, float]

class ComponentSimulator:
    def __init__(self, config: ComponentConfig):
        self.config = config
        self.current_state = config.initial_state

    def step(self, time: datetime, inputs: Dict[str, float]) -> Dict[str, float]:
        """
        Simulate one time step for the component
        Returns dict with output values (e.g., power, state of charge)
        """
        raise NotImplementedError

class BatterySimulator(ComponentSimulator):
    def step(self, time: datetime, inputs: Dict[str, float]) -> Dict[str, float]:
        power_request = inputs.get('power_request', 0)
        
        # Apply efficiency losses
        actual_power = power_request * self.config.efficiency if power_request > 0 else power_request / self.config.efficiency
        
        # Update state of charge
        new_state = self.current_state + (actual_power / self.config.capacity)
        new_state = max(0, min(1, new_state))
        
        self.current_state = new_state
        
        return {
            'power_output': actual_power,
            'state_of_charge': new_state
        }

class VPPSimulator:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.components = {}
        self.current_time = config.start_time
        
        for component_id, comp_config in config.components.items():
            if comp_config.type == 'battery':
                self.components[component_id] = BatterySimulator(comp_config)
            # Add other component types as needed
    
    def step(self, dispatch_commands: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """
        Simulate one time step for all components
        Returns dict with component outputs
        """
        results = {}
        for component_id, component in self.components.items():
            inputs = dispatch_commands.get(component_id, {})
            results[component_id] = component.step(self.current_time, inputs)
        
        self.current_time += self.config.time_step
        return results 