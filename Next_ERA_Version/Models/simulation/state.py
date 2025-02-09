from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class SimulationState:
    """Base class for all simulation states"""
    component_type: str
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__

@dataclass
class StorageState(SimulationState):
    capacity: float
    current_charge: float
    charge_rate: float
    discharge_rate: float

@dataclass
class SourceState(SimulationState):
    max_power_output: float
    current_output: float
    availability: float

@dataclass
class ProtocolState(SimulationState):
    mode: str
    parameters: Dict[str, Any] 