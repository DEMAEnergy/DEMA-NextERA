from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import random
from .base_simulator import BaseSimulator
from .grid_operator_model import GridOperatorModel

class GridOperatorSimulator(BaseSimulator):
    """Simulator for grid operator behavior"""
    
    def __init__(self, model: GridOperatorModel, config: Dict[str, Any]):
        super().__init__(model, config)
        self.noise_factors = config.get('noise_factors', {
            'frequency': 0.01,  # Hz variation
            'voltage': 0.005,   # per unit variation
            'load': 0.02       # load variation factor
        })
        
    def step(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate one time step of grid operator behavior
        
        Args:
            inputs: Dict containing:
                - load_forecast: Expected load for next period
                - generation_forecast: Expected generation for next period
                - grid_events: List of any grid events/disturbances
                
        Returns:
            Dict with simulation results including grid state and operator decisions
        """
        # Update time
        self.current_time += timedelta(seconds=self.time_step)
        
        # Extract inputs with defaults
        load_forecast = inputs.get('load_forecast', self.model.current_state['total_load'])
        generation_forecast = inputs.get('generation_forecast', self.model.current_state['total_generation'])
        grid_events = inputs.get('grid_events', [])
        
        # Simulate grid parameter variations
        new_state = {
            'grid_frequency': self._simulate_frequency(),
            'grid_voltage': self._simulate_voltage(),
            'total_load': self._simulate_load(load_forecast),
            'total_generation': generation_forecast,
            'congestion_points': self._simulate_congestion(grid_events)
        }
        
        # Update model state
        self.model.update_state(new_state)
        
        # Evaluate grid stability
        new_state['grid_stability_index'] = self.model.evaluate_grid_stability()
        
        # Check for constraint violations
        new_state['active_constraints'] = self.model.check_constraints()
        
        # Generate operator response
        response = self._generate_operator_response(new_state)
        
        # Save state
        self.save_state(new_state)
        
        return response
    
    def _simulate_frequency(self) -> float:
        """Simulate grid frequency variations"""
        base_frequency = self.model.current_state['grid_frequency']
        noise = random.uniform(-self.noise_factors['frequency'], 
                             self.noise_factors['frequency'])
        return base_frequency + noise
    
    def _simulate_voltage(self) -> float:
        """Simulate voltage variations"""
        base_voltage = self.model.current_state['grid_voltage']
        noise = random.uniform(-self.noise_factors['voltage'], 
                             self.noise_factors['voltage'])
        return base_voltage + noise
    
    def _simulate_load(self, forecast: float) -> float:
        """Simulate actual load with some variation from forecast"""
        variation = forecast * random.uniform(-self.noise_factors['load'], 
                                           self.noise_factors['load'])
        return forecast + variation
    
    def _simulate_congestion(self, events: list) -> list:
        """Simulate grid congestion points based on events"""
        congestion_points = []
        for event in events:
            if event.get('type') == 'congestion':
                congestion_points.append({
                    'location': event['location'],
                    'severity': event['severity']
                })
        return congestion_points
    
    def _generate_operator_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate grid operator response based on current state"""
        response = {
            'timestamp': self.current_time,
            'grid_state': state,
            'operator_actions': []
        }
        
        # Handle constraint violations
        if state['active_constraints']:
            response['operator_actions'].append({
                'action_type': 'constraint_violation_response',
                'violations': state['active_constraints'],
                'priority': 'high'
            })
            
        # Handle low stability
        if state['grid_stability_index'] < 0.8:
            response['operator_actions'].append({
                'action_type': 'stability_improvement',
                'current_index': state['grid_stability_index'],
                'priority': 'medium'
            })
            
        # Handle congestion
        if state['congestion_points']:
            response['operator_actions'].append({
                'action_type': 'congestion_management',
                'congestion_points': state['congestion_points'],
                'priority': 'medium'
            })
            
        return response 