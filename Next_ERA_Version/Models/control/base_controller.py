from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from ..base_model import BaseModel, ResourceStatus

class ControlMode(Enum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    EMERGENCY = "emergency"
    MAINTENANCE = "maintenance"
    OPTIMIZATION = "optimization"

class ControlPriority(Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3

class BaseController:
    """Base class for all resource controllers"""
    
    def __init__(self, model: BaseModel, config: Dict[str, Any]):
        self.model = model
        self.config = config
        self.setpoint_history = []
        self.last_control_action = datetime.now()
        self.control_interval = config.get('control_interval', 60)  # seconds
        self.mode = ControlMode.AUTOMATIC
        self.priority = ControlPriority.MEDIUM
        self.safety_limits = config.get('safety_limits', {
            'max_rate_of_change': 0.1,  # per second
            'max_deviation': 0.2,       # from setpoint
            'response_timeout': 30.0     # seconds
        })
        self.performance_metrics = {
            'tracking_error': 0.0,
            'response_time': 0.0,
            'stability_index': 1.0,
            'energy_efficiency': 1.0
        }
        
    def update(
        self, 
        current_state: Dict[str, Any], 
        target_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update control outputs based on current and target states
        Returns control actions to be taken
        """
        # Check if control action is allowed
        if not self._can_control():
            return {'action': 'none', 'reason': 'control_not_allowed'}
            
        # Calculate control error
        error = self._calculate_error(current_state, target_state)
        
        # Check safety constraints
        if not self._check_safety_constraints(error):
            return self._handle_safety_violation()
            
        # Calculate control action
        action = self._calculate_control_action(error)
        
        # Validate action
        if not self.validate_setpoint(action.get('setpoint', 0)):
            return self._handle_invalid_setpoint(action)
            
        # Log action
        self.log_control_action(action)
        
        # Update performance metrics
        self._update_performance_metrics(error, action)
        
        return action
        
    def validate_setpoint(self, setpoint: float) -> bool:
        """Validate if setpoint is within acceptable range"""
        if not isinstance(setpoint, (int, float)):
            return False
            
        # Check against model capacity
        if abs(setpoint) > self.model.capacity:
            return False
            
        # Check rate of change
        if self.setpoint_history:
            last_setpoint = self.setpoint_history[-1]['action'].get('setpoint', 0)
            time_diff = (datetime.now() - self.last_control_action).total_seconds()
            if time_diff > 0:
                rate_of_change = abs(setpoint - last_setpoint) / time_diff
                if rate_of_change > self.safety_limits['max_rate_of_change']:
                    return False
                    
        return True
        
    def log_control_action(self, action: Dict[str, Any]):
        """Log control action for history"""
        self.setpoint_history.append({
            'timestamp': datetime.now(),
            'action': action,
            'mode': self.mode,
            'priority': self.priority
        })
        self.last_control_action = datetime.now()
        
    def get_control_history(self) -> list:
        """Get history of control actions"""
        return self.setpoint_history
        
    def set_mode(self, mode: ControlMode):
        """Set controller mode"""
        self.mode = mode
        
    def set_priority(self, priority: ControlPriority):
        """Set controller priority"""
        self.priority = priority
        
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get current performance metrics"""
        return self.performance_metrics
        
    def _can_control(self) -> bool:
        """Check if control action is allowed"""
        # Check resource status
        if self.model.status in [ResourceStatus.ERROR, ResourceStatus.MAINTENANCE]:
            return False
            
        # Check control interval
        time_since_last = (datetime.now() - self.last_control_action).total_seconds()
        if time_since_last < self.control_interval:
            return False
            
        # Check resource availability
        if not self.model.is_available():
            return False
            
        return True
        
    def _calculate_error(
        self, current_state: Dict[str, Any], target_state: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate control error"""
        raise NotImplementedError
        
    def _check_safety_constraints(self, error: Dict[str, float]) -> bool:
        """Check if safety constraints are satisfied"""
        # Check maximum deviation
        if abs(error.get('total', 0)) > self.safety_limits['max_deviation']:
            return False
            
        # Check response timeout
        if error.get('duration', 0) > self.safety_limits['response_timeout']:
            return False
            
        return True
        
    def _handle_safety_violation(self) -> Dict[str, Any]:
        """Handle safety constraint violation"""
        self.mode = ControlMode.EMERGENCY
        self.model.handle_emergency('safety_constraint_violation')
        return {
            'action': 'emergency_stop',
            'reason': 'safety_constraint_violation'
        }
        
    def _handle_invalid_setpoint(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invalid setpoint"""
        return {
            'action': 'limit',
            'original': action,
            'reason': 'invalid_setpoint'
        }
        
    def _calculate_control_action(self, error: Dict[str, float]) -> Dict[str, Any]:
        """Calculate control action based on error"""
        raise NotImplementedError
        
    def _update_performance_metrics(
        self, error: Dict[str, float], action: Dict[str, Any]
    ):
        """Update controller performance metrics"""
        # Update tracking error
        self.performance_metrics['tracking_error'] = abs(error.get('total', 0))
        
        # Update response time
        self.performance_metrics['response_time'] = error.get('duration', 0)
        
        # Update stability index (based on setpoint changes)
        if len(self.setpoint_history) > 1:
            last_setpoint = self.setpoint_history[-1]['action'].get('setpoint', 0)
            new_setpoint = action.get('setpoint', 0)
            stability = 1.0 - min(1.0, abs(new_setpoint - last_setpoint) / self.model.capacity)
            self.performance_metrics['stability_index'] = stability
            
        # Update energy efficiency
        if 'power' in action:
            actual_power = action['power']
            optimal_power = action.get('optimal_power', actual_power)
            if optimal_power != 0:
                efficiency = min(1.0, actual_power / optimal_power)
                self.performance_metrics['energy_efficiency'] = efficiency 