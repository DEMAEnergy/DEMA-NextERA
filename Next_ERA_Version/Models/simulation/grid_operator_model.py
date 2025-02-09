from typing import Dict, Any, Optional
from datetime import datetime
from ..base_model import BaseModel

class GridOperatorModel(BaseModel):
    """Model representing a grid operator's behavior and state"""
    
    def __init__(self, resource_id: str, config: Dict[str, Any]):
        super().__init__(resource_id, config)
        self.grid_constraints = config.get('grid_constraints', {
            'voltage_limits': {'min': 0.95, 'max': 1.05},  # per unit
            'frequency_limits': {'min': 49.8, 'max': 50.2},  # Hz
            'power_limits': {'min': 0, 'max': 100000},  # kW
        })
        self.current_state = {
            'grid_frequency': 50.0,
            'grid_voltage': 1.0,
            'total_load': 0.0,
            'total_generation': 0.0,
            'grid_stability_index': 1.0,
            'congestion_points': [],
            'active_constraints': []
        }
        self.dispatch_requests = []
        
    def update_state(self, new_state: Dict[str, Any]):
        """Update the grid operator's current state"""
        self.current_state.update(new_state)
        
    def get_status(self) -> Dict[str, Any]:
        """Get current grid operator status"""
        return {
            'timestamp': datetime.now(),
            'state': self.current_state,
            'constraints': self.grid_constraints,
            'pending_requests': len(self.dispatch_requests)
        }
        
    def add_dispatch_request(self, request: Dict[str, Any]):
        """Add a new dispatch request to the queue"""
        self.dispatch_requests.append({
            'timestamp': datetime.now(),
            'request': request,
            'status': 'pending'
        })
        
    def evaluate_grid_stability(self) -> float:
        """
        Evaluate current grid stability based on various parameters
        Returns a value between 0 (unstable) and 1 (perfectly stable)
        """
        frequency_deviation = abs(self.current_state['grid_frequency'] - 50.0) / 0.2
        voltage_deviation = abs(self.current_state['grid_voltage'] - 1.0) / 0.05
        power_balance = abs(self.current_state['total_generation'] - self.current_state['total_load'])
        
        stability_index = 1.0 - (frequency_deviation * 0.4 + voltage_deviation * 0.4 + 
                               (power_balance / self.grid_constraints['power_limits']['max']) * 0.2)
        return max(0.0, min(1.0, stability_index))
        
    def check_constraints(self) -> list:
        """Check for any violated grid constraints"""
        violations = []
        
        if not (self.grid_constraints['frequency_limits']['min'] <= 
                self.current_state['grid_frequency'] <= 
                self.grid_constraints['frequency_limits']['max']):
            violations.append('frequency_violation')
            
        if not (self.grid_constraints['voltage_limits']['min'] <= 
                self.current_state['grid_voltage'] <= 
                self.grid_constraints['voltage_limits']['max']):
            violations.append('voltage_violation')
            
        if self.current_state['total_load'] > self.grid_constraints['power_limits']['max']:
            violations.append('power_limit_violation')
            
        return violations 