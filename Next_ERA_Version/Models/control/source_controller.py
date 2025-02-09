from typing import Dict, Any
from datetime import datetime
import numpy as np
from .base_controller import BaseController, ControlMode, ControlPriority
from ..Source.pv_system import PVSystem
from ..Source.wind_turbine import WindTurbine

class PVController(BaseController):
    """Controller for PV systems"""
    
    def __init__(self, model: PVSystem, config: Dict[str, Any]):
        super().__init__(model, config)
        # Control parameters
        self.power_tolerance = config.get('power_tolerance', 0.05)
        self.inverter_control_delay = config.get('inverter_control_delay', 1)
        self.pid_params = config.get('pid_params', {
            'kp': 1.0,  # Proportional gain
            'ki': 0.1,  # Integral gain
            'kd': 0.05  # Derivative gain
        })
        # State variables
        self.integral_error = 0.0
        self.last_error = 0.0
        # Operating parameters
        self.operating_params = config.get('operating_params', {
            'min_power_factor': 0.9,
            'max_ramp_rate': 0.2,      # Fraction of capacity per second
            'curtailment_threshold': 0.9  # Fraction of capacity
        })
        
    def _calculate_error(
        self, current_state: Dict[str, Any], target_state: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate control error with multiple factors"""
        current_power = current_state.get('current_power', 0)
        target_power = target_state.get('power_setpoint', 0)
        irradiance = current_state.get('irradiance', 0)
        panel_temp = current_state.get('panel_temperature', 25)
        
        # Calculate maximum available power
        max_power = self.model.calculate_power_output(irradiance, panel_temp)
        
        # Power tracking error
        if target_power > max_power:
            power_error = 0  # Can't produce more than available
        else:
            power_error = (target_power - current_power) / self.model.capacity
            
        # Calculate integral and derivative terms
        dt = (datetime.now() - self.last_control_action).total_seconds()
        if dt > 0:
            self.integral_error += power_error * dt
            derivative_error = (power_error - self.last_error) / dt
            self.last_error = power_error
        else:
            derivative_error = 0
            
        # Calculate ramp rate
        if len(self.setpoint_history) > 0:
            last_power = self.setpoint_history[-1]['action'].get('power', current_power)
            ramp_rate = (current_power - last_power) / (dt * self.model.capacity) if dt > 0 else 0
        else:
            ramp_rate = 0
            
        return {
            'power': power_error,
            'integral': self.integral_error,
            'derivative': derivative_error,
            'ramp_rate': ramp_rate,
            'available_power': max_power,
            'total': power_error,
            'duration': dt
        }
        
    def _calculate_control_action(self, error: Dict[str, float]) -> Dict[str, Any]:
        """Calculate control action using PID control with power constraints"""
        # PID control
        p_term = self.pid_params['kp'] * error['power']
        i_term = self.pid_params['ki'] * error['integral']
        d_term = self.pid_params['kd'] * error['derivative']
        
        # Calculate power change
        power_change = (p_term + i_term + d_term) * self.model.capacity
        
        # Apply ramp rate limit
        max_change = self.operating_params['max_ramp_rate'] * self.model.capacity * error['duration']
        if abs(power_change) > max_change:
            power_change = np.sign(power_change) * max_change
            
        # Calculate new power setpoint
        current_power = self.model.current_output
        new_power = current_power + power_change
        
        # Apply power limits
        max_power = min(
            error['available_power'],
            self.model.capacity * self.operating_params['curtailment_threshold']
        )
        new_power = np.clip(new_power, 0, max_power)
        
        return {
            'command': 'set_power',
            'power': new_power,
            'setpoint': new_power,
            'power_factor': self.operating_params['min_power_factor'],
            'optimal_power': error['available_power']
        }

class WindTurbineController(BaseController):
    """Controller for wind turbines"""
    
    def __init__(self, model: WindTurbine, config: Dict[str, Any]):
        super().__init__(model, config)
        # Control parameters
        self.yaw_tolerance = config.get('yaw_tolerance', 5)  # degrees
        self.pitch_control_rate = config.get('pitch_control_rate', 5)  # degrees per second
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
            'min_pitch': -2.0,    # degrees
            'max_pitch': 90.0,    # degrees
            'optimal_tsr': 7.0,   # Tip speed ratio
            'yaw_rate': 2.0,      # degrees per second
            'pitch_rate': 5.0     # degrees per second
        })
        
    def _calculate_error(
        self, current_state: Dict[str, Any], target_state: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate control error with multiple factors"""
        wind_speed = current_state.get('wind_speed', 0)
        wind_direction = current_state.get('wind_direction', 0)
        current_power = current_state.get('current_power', 0)
        rotor_speed = current_state.get('rotor_speed', 0)
        current_pitch = current_state.get('pitch_angle', 0)
        current_yaw = current_state.get('yaw_angle', 0)
        
        # Calculate optimal tip speed ratio
        if wind_speed > 0:
            current_tsr = (rotor_speed * self.model.rotor_diameter/2) / wind_speed
            tsr_error = current_tsr - self.operating_params['optimal_tsr']
        else:
            tsr_error = 0
            
        # Calculate yaw error
        yaw_error = wind_direction - current_yaw
        if abs(yaw_error) > 180:  # Normalize to [-180, 180]
            yaw_error = yaw_error - np.sign(yaw_error) * 360
            
        # Calculate power error
        target_power = target_state.get('power_setpoint', self.model.get_power_curve_value(wind_speed))
        power_error = (target_power - current_power) / self.model.capacity
        
        # Calculate integral and derivative terms
        dt = (datetime.now() - self.last_control_action).total_seconds()
        if dt > 0:
            self.integral_error += power_error * dt
            derivative_error = (power_error - self.last_error) / dt
            self.last_error = power_error
        else:
            derivative_error = 0
            
        return {
            'power': power_error,
            'tsr': tsr_error,
            'yaw': yaw_error,
            'integral': self.integral_error,
            'derivative': derivative_error,
            'wind_speed': wind_speed,
            'total': power_error + 0.2 * tsr_error + 0.1 * abs(yaw_error),
            'duration': dt
        }
        
    def _calculate_control_action(self, error: Dict[str, float]) -> Dict[str, Any]:
        """Calculate control action using PID control with turbine constraints"""
        wind_speed = error['wind_speed']
        
        # Check operating conditions
        if wind_speed < self.model.cut_in_speed:
            return {
                'command': 'stop',
                'reason': 'below_cut_in'
            }
        elif wind_speed > self.model.cut_out_speed:
            return {
                'command': 'brake',
                'reason': 'above_cut_out'
            }
            
        # PID control for power regulation
        p_term = self.pid_params['kp'] * error['power']
        i_term = self.pid_params['ki'] * error['integral']
        d_term = self.pid_params['kd'] * error['derivative']
        
        # Calculate pitch angle change
        if wind_speed > self.model.rated_wind_speed:
            # Above rated: pitch for power control
            pitch_change = p_term + i_term + d_term
        else:
            # Below rated: pitch for optimal TSR
            pitch_change = 0.5 * error['tsr']
            
        # Apply pitch rate limit
        max_pitch_change = self.operating_params['pitch_rate'] * error['duration']
        pitch_change = np.clip(pitch_change, -max_pitch_change, max_pitch_change)
        
        # Calculate yaw adjustment
        if abs(error['yaw']) > self.yaw_tolerance:
            yaw_change = np.clip(
                error['yaw'],
                -self.operating_params['yaw_rate'] * error['duration'],
                self.operating_params['yaw_rate'] * error['duration']
            )
        else:
            yaw_change = 0
            
        # Calculate optimal power
        optimal_power = self.model.get_power_curve_value(wind_speed)
        
        return {
            'command': 'adjust_turbine',
            'pitch_angle': np.clip(
                pitch_change,
                self.operating_params['min_pitch'],
                self.operating_params['max_pitch']
            ),
            'yaw_angle': yaw_change,
            'setpoint': optimal_power,
            'optimal_power': optimal_power
        } 