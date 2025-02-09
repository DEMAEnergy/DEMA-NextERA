from typing import Dict, Any
from datetime import datetime
from .base_controller import BaseController, ControlMode, ControlPriority
from ..Load.hvac import HVAC
from ..Load.motor import Motor
from ..Load.data_center_cooling import DataCenterCooling
import numpy as np

class HVACController(BaseController):
    """Controller for HVAC systems"""
    
    def __init__(self, model: HVAC, config: Dict[str, Any]):
        super().__init__(model, config)
        # Control parameters
        self.temp_deadband = config.get('temperature_deadband', 1.0)
        self.min_cycle_time = config.get('min_cycle_time', 300)  # seconds
        self.pid_params = config.get('pid_params', {
            'kp': 100.0,  # Proportional gain
            'ki': 0.1,    # Integral gain
            'kd': 10.0    # Derivative gain
        })
        # State variables
        self.integral_error = 0.0
        self.last_error = 0.0
        self.last_cycle_time = datetime.now()
        # Comfort parameters
        self.comfort_bounds = config.get('comfort_bounds', {
            'temperature': {'min': 20.0, 'max': 26.0},
            'humidity': {'min': 30.0, 'max': 60.0}
        })
        
    def _calculate_error(
        self, current_state: Dict[str, Any], target_state: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate control error with multiple factors"""
        current_temp = current_state.get('current_temperature', 0)
        target_temp = target_state.get('temperature_setpoint', self.model.temperature_setpoint)
        current_humidity = current_state.get('humidity', 50.0)
        
        # Temperature error
        temp_error = current_temp - target_temp
        
        # Humidity penalty
        humidity_bounds = self.comfort_bounds['humidity']
        if current_humidity < humidity_bounds['min']:
            humidity_error = current_humidity - humidity_bounds['min']
        elif current_humidity > humidity_bounds['max']:
            humidity_error = current_humidity - humidity_bounds['max']
        else:
            humidity_error = 0.0
            
        # Calculate integral and derivative terms
        dt = (datetime.now() - self.last_control_action).total_seconds()
        if dt > 0:
            self.integral_error += temp_error * dt
            derivative_error = (temp_error - self.last_error) / dt
            self.last_error = temp_error
        else:
            derivative_error = 0
            
        return {
            'temperature': temp_error,
            'humidity': humidity_error,
            'integral': self.integral_error,
            'derivative': derivative_error,
            'total': temp_error + 0.2 * humidity_error,  # Weighted sum
            'duration': dt
        }
        
    def _calculate_control_action(self, error: Dict[str, float]) -> Dict[str, Any]:
        """Calculate control action using PID control"""
        # PID control
        p_term = self.pid_params['kp'] * error['temperature']
        i_term = self.pid_params['ki'] * error['integral']
        d_term = self.pid_params['kd'] * error['derivative']
        
        # Calculate power setpoint
        power_setpoint = p_term + i_term + d_term
        
        # Apply comfort-based limits
        temp_bounds = self.comfort_bounds['temperature']
        if error['temperature'] > 0 and power_setpoint > 0:  # Too hot
            power_setpoint = min(
                power_setpoint,
                self.model.capacity * (error['temperature'] / (temp_bounds['max'] - temp_bounds['min']))
            )
        elif error['temperature'] < 0 and power_setpoint < 0:  # Too cold
            power_setpoint = max(
                power_setpoint,
                -self.model.capacity * (abs(error['temperature']) / (temp_bounds['max'] - temp_bounds['min']))
            )
            
        # Check minimum cycle time
        time_since_last_cycle = (datetime.now() - self.last_cycle_time).total_seconds()
        if time_since_last_cycle < self.min_cycle_time:
            if abs(error['total']) < self.temp_deadband:
                return {'command': 'maintain'}
                
        # Update cycle time if changing state
        if (power_setpoint > 0 and self.model.current_power == 0) or \
           (power_setpoint == 0 and self.model.current_power > 0):
            self.last_cycle_time = datetime.now()
            
        return {
            'command': 'set_power',
            'power': power_setpoint,
            'setpoint': power_setpoint,
            'temperature_setpoint': self.model.temperature_setpoint,
            'optimal_power': abs(error['temperature']) * 100  # Ideal power for perfect tracking
        }

class MotorController(BaseController):
    """Controller for electric motors"""
    
    def __init__(self, model: Motor, config: Dict[str, Any]):
        super().__init__(model, config)
        # Control parameters
        self.speed_tolerance = config.get('speed_tolerance', 0.02)  # 2%
        self.ramp_rate = config.get('ramp_rate', 10)  # RPM per second
        self.pid_params = config.get('pid_params', {
            'kp': 0.5,  # Proportional gain
            'ki': 0.1,  # Integral gain
            'kd': 0.05  # Derivative gain
        })
        # State variables
        self.integral_error = 0.0
        self.last_error = 0.0
        # Operating limits
        self.operating_limits = config.get('operating_limits', {
            'max_acceleration': 20.0,  # RPM/s²
            'max_jerk': 5.0,          # RPM/s³
            'min_speed': 0.1,         # Fraction of rated speed
            'max_speed': 1.0          # Fraction of rated speed
        })
        
    def _calculate_error(
        self, current_state: Dict[str, Any], target_state: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate control error with multiple factors"""
        current_speed = current_state.get('current_speed', 0)
        target_speed = target_state.get('speed_setpoint', 0)
        current_torque = current_state.get('torque', 0)
        rated_speed = self.model.rated_speed
        
        # Speed error
        speed_error = (target_speed - current_speed) / rated_speed
        
        # Calculate integral and derivative terms
        dt = (datetime.now() - self.last_control_action).total_seconds()
        if dt > 0:
            self.integral_error += speed_error * dt
            derivative_error = (speed_error - self.last_error) / dt
            self.last_error = speed_error
        else:
            derivative_error = 0
            
        # Calculate acceleration
        if len(self.setpoint_history) > 0:
            last_speed = self.setpoint_history[-1]['action'].get('speed', current_speed)
            acceleration = (current_speed - last_speed) / dt if dt > 0 else 0
        else:
            acceleration = 0
            
        return {
            'speed': speed_error,
            'acceleration': acceleration,
            'integral': self.integral_error,
            'derivative': derivative_error,
            'total': speed_error,
            'duration': dt
        }
        
    def _calculate_control_action(self, error: Dict[str, float]) -> Dict[str, Any]:
        """Calculate control action using PID control with motion constraints"""
        # PID control
        p_term = self.pid_params['kp'] * error['speed']
        i_term = self.pid_params['ki'] * error['integral']
        d_term = self.pid_params['kd'] * error['derivative']
        
        # Calculate speed change
        speed_change = (p_term + i_term + d_term) * self.model.rated_speed
        
        # Apply motion constraints
        max_speed_change = self.ramp_rate * error['duration']
        if abs(speed_change) > max_speed_change:
            speed_change = np.sign(speed_change) * max_speed_change
            
        # Check acceleration limit
        if abs(error['acceleration']) > self.operating_limits['max_acceleration']:
            speed_change *= 0.5  # Reduce change if accelerating too fast
            
        # Calculate new speed
        current_speed = self.model.current_speed
        new_speed = current_speed + speed_change
        
        # Apply speed limits
        min_speed = self.operating_limits['min_speed'] * self.model.rated_speed
        max_speed = self.operating_limits['max_speed'] * self.model.rated_speed
        new_speed = np.clip(new_speed, min_speed, max_speed)
        
        return {
            'command': 'set_speed',
            'speed': new_speed,
            'setpoint': new_speed,
            'acceleration': error['acceleration'],
            'optimal_speed': current_speed + error['speed'] * self.model.rated_speed
        }

class DataCenterCoolingController(BaseController):
    """Controller for data center cooling systems"""
    
    def __init__(self, model: DataCenterCooling, config: Dict[str, Any]):
        super().__init__(model, config)
        # Control parameters
        self.temp_tolerance = config.get('temperature_tolerance', 0.5)
        self.flow_rate_deadband = config.get('flow_rate_deadband', 0.05)
        self.pid_params = config.get('pid_params', {
            'kp': 1.0,  # Proportional gain
            'ki': 0.1,  # Integral gain
            'kd': 0.2   # Derivative gain
        })
        # State variables
        self.integral_error = 0.0
        self.last_error = 0.0
        # Operating parameters
        self.operating_params = config.get('operating_params', {
            'min_flow_rate': 0.1,     # Fraction of max flow
            'max_flow_rate': 1.0,     # Fraction of max flow
            'oil_water_ratio': 1.2,   # Water flow multiplier
            'temp_approach': 5.0      # Minimum temperature approach (°C)
        })
        
    def _calculate_error(
        self, current_state: Dict[str, Any], target_state: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate control error with multiple factors"""
        # Get temperatures
        current_temp = current_state.get('current_temperature', 0)
        target_temp = target_state.get('temperature_setpoint', self.model.temperature_setpoint)
        oil_temp = current_state.get('oil_temperature', 0)
        water_temp = current_state.get('water_temperature', 0)
        
        # Temperature errors
        room_temp_error = current_temp - target_temp
        approach_temp_error = oil_temp - water_temp - self.operating_params['temp_approach']
        
        # Calculate integral and derivative terms
        dt = (datetime.now() - self.last_control_action).total_seconds()
        if dt > 0:
            self.integral_error += room_temp_error * dt
            derivative_error = (room_temp_error - self.last_error) / dt
            self.last_error = room_temp_error
        else:
            derivative_error = 0
            
        return {
            'room_temperature': room_temp_error,
            'approach_temperature': approach_temp_error,
            'integral': self.integral_error,
            'derivative': derivative_error,
            'total': room_temp_error + 0.5 * approach_temp_error,
            'duration': dt
        }
        
    def _calculate_control_action(self, error: Dict[str, float]) -> Dict[str, Any]:
        """Calculate control action using PID control with flow optimization"""
        # PID control for room temperature
        p_term = self.pid_params['kp'] * error['room_temperature']
        i_term = self.pid_params['ki'] * error['integral']
        d_term = self.pid_params['kd'] * error['derivative']
        
        # Calculate base flow rate
        base_flow = p_term + i_term + d_term
        
        # Adjust for approach temperature
        if error['approach_temperature'] > 0:
            base_flow *= (1 + 0.2 * error['approach_temperature'])
            
        # Apply flow limits
        base_flow = np.clip(
            base_flow,
            self.operating_params['min_flow_rate'] * self.model.capacity,
            self.operating_params['max_flow_rate'] * self.model.capacity
        )
        
        # Calculate water flow based on oil flow
        water_flow = base_flow * self.operating_params['oil_water_ratio']
        
        return {
            'command': 'update_flow_rates',
            'oil_flow': base_flow,
            'water_flow': water_flow,
            'setpoint': base_flow,
            'temperature_setpoint': self.model.temperature_setpoint,
            'optimal_flow': abs(error['room_temperature']) * 0.1 * self.model.capacity
        } 