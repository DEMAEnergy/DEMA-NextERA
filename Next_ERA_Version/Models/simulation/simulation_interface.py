from typing import Protocol, Dict, Any

class SimulationInterface(Protocol):
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the simulation with configuration"""
        pass
    
    def step(self, time_delta: float) -> SimulationState:
        """Advance simulation by time_delta"""
        pass
    
    def reset(self) -> None:
        """Reset simulation to initial state"""
        pass
    
    def get_current_state(self) -> SimulationState:
        """Get current simulation state"""
        pass 