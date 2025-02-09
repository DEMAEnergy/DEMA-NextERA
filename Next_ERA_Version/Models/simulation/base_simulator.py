from typing import Dict, Any, Optional
from datetime import datetime
from ..base_model import BaseModel
from abc import ABC, abstractmethod
from .state import SimulationState

class BaseSimulator(ABC):
    """Base class for all resource simulators"""
    
    def __init__(self, model: BaseModel, config: Dict[str, Any]):
        self.model = model
        self.config = config
        self.time_step = config.get('time_step', 60)  # seconds
        self.current_time = datetime.now()
        self.history = []
        
    def step(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate one time step
        Returns dict with simulation results
        """
        raise NotImplementedError
        
    def reset(self):
        """Reset simulator to initial state"""
        self.current_time = datetime.now()
        self.history = []
        
    def get_history(self) -> list:
        """Get simulation history"""
        return self.history
        
    def save_state(self, state: Dict[str, Any]):
        """Save current state to history"""
        self.history.append({
            'timestamp': self.current_time,
            'state': state
        })

    @abstractmethod
    def get_state(self) -> SimulationState:
        pass
    
    @abstractmethod
    def update_state(self, new_state: SimulationState) -> None:
        pass
    
    @abstractmethod
    def validate_state(self, state: SimulationState) -> bool:
        pass 