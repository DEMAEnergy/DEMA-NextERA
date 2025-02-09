from typing import Dict, Any
from datetime import datetime
from .base_simulator import BaseSimulator
from .state import LoadState
from ..Load.hvac import HVAC
from ..Load.motor import Motor
import numpy as np

class HVACSimulator(BaseSimulator):
    """Simulator for HVAC systems"""
    
    def __init__(self, model: HVAC, config: Dict[str, Any]):
        super().__init__(model, config)
        self.thermal_model = config.get('thermal_model', 'advanced')
        self.cop_model = config.get('cop_model', 'dynamic')
        self.market_enabled = config.get('market_enabled', False)
        self.dr_enabled = config.get('demand_response_enabled', True)
        
    def step(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ambient_temp = inputs.get('ambient_temperature', 25.0)
        thermal_load = inputs.get('thermal_load', 0.0)
        humidity = inputs.get('humidity', 50.0)
        occupancy = inputs.get('occupancy', 1.0)
        market_price = inputs.get('market_price', None)
        dr_signal = inputs.get('demand_response_signal', None)
        
        # Calculate dynamic COP
        cop = self._calculate_cop(ambient_temp)
        
        # Calculate base power consumption
        power = self._calculate_power_consumption(
            ambient_temp, thermal_load, humidity, cop
        )
        
        # Apply demand response if enabled
        if self.dr_enabled and dr_signal is not None:
            power = self._apply_demand_response(power, dr_signal)
            
        # Market optimization if enabled
        if self.market_enabled and market_price is not None:
            power = self._optimize_market_position(power, market_price)
        
        # Update temperature based on thermal model
        if self.thermal_model == 'advanced':
            self._update_temperature(
                power, ambient_temp, thermal_load, humidity, occupancy
            )
            
        # Update model state
        self.model.update_power_consumption(power)
        
        # Get and save state
        state = self.get_state()
        self.save_state(state.to_dict())
        
        return state.to_dict()
        
    def _calculate_cop(self, ambient_temp: float) -> float:
        """Calculate COP based on ambient temperature"""
        if self.cop_model == 'dynamic':
            # Carnot efficiency based model
            t_indoor = self.model.current_temperature + 273.15  # K
            t_ambient = ambient_temp + 273.15  # K
            carnot_cop = t_indoor / (t_ambient - t_indoor)
            
            # Real systems achieve ~50% of Carnot efficiency
            real_cop = 0.5 * abs(carnot_cop)
            
            # Bound COP within realistic limits
            return max(1.5, min(5.0, real_cop))
        else:
            return self.model.nominal_cop
            
    def _calculate_power_consumption(
        self, ambient_temp: float, thermal_load: float, 
        humidity: float, cop: float
    ) -> float:
        """Calculate power consumption with humidity effects"""
        # Base cooling load
        sensible_load = thermal_load
        
        # Add latent load from humidity
        latent_heat = 2260  # kJ/kg
        moisture_load = max(0, humidity - 50) * 0.01 * latent_heat
        total_load = sensible_load + moisture_load
        
        # Convert to power
        return total_load / cop
        
    def _update_temperature(
        self, power: float, ambient_temp: float, thermal_load: float,
        humidity: float, occupancy: float
    ):
        """Advanced thermal model for temperature evolution"""
        # Thermal mass properties
        mass = self.config.get('thermal_mass', 2000)  # kg
        specific_heat = self.config.get('specific_heat', 1.0)  # kJ/kg·K
        thermal_capacity = mass * specific_heat
        
        # Heat transfer coefficient
        u_value = self.config.get('u_value', 0.5)  # W/m²·K
        surface_area = self.config.get('surface_area', 200)  # m²
        
        # Calculate heat flows
        cooling_effect = power * self.model.cop
        heat_gain_ambient = u_value * surface_area * (ambient_temp - self.model.current_temperature)
        heat_gain_internal = thermal_load * occupancy
        heat_gain_latent = max(0, humidity - 50) * 10  # Simplified latent heat gain
        
        # Net heat flow
        net_heat = heat_gain_ambient + heat_gain_internal + heat_gain_latent - cooling_effect
        
        # Temperature change
        delta_t = net_heat / thermal_capacity * self.time_step
        self.model.current_temperature += delta_t
        
    def _apply_demand_response(self, power: float, dr_signal: Dict[str, Any]) -> float:
        """Apply demand response signal"""
        dr_type = dr_signal.get('type', 'none')
        dr_value = dr_signal.get('value', 0.0)
        
        if dr_type == 'curtailment':
            return power * (1 - dr_value)
        elif dr_type == 'shift':
            temp_adjustment = dr_value
            self.model.setpoint += temp_adjustment
            return power
        return power
        
    def _optimize_market_position(self, power: float, market_price: float) -> float:
        """Optimize consumption based on market price"""
        threshold_high = self.config.get('price_threshold_high', 100)
        comfort_band = self.config.get('comfort_band', 2.0)
        
        if market_price > threshold_high:
            # Allow temperature to float within comfort band
            self.model.setpoint += comfort_band
            return power * 0.7
        else:
            # Return to normal setpoint
            self.model.setpoint = self.model.nominal_setpoint
            return power

    def get_state(self) -> LoadState:
        """Get current simulation state"""
        return LoadState(
            component_type="hvac",
            timestamp=datetime.now().timestamp(),
            power_consumption=self.model.current_power,
            temperature=self.model.current_temperature,
            setpoint=self.model.setpoint,
            cop=self.model.cop
        )
        
    def update_state(self, new_state: LoadState) -> None:
        """Update simulation state"""
        self.model.current_power = new_state.power_consumption
        self.model.current_temperature = new_state.temperature
        self.model.setpoint = new_state.setpoint
        self.model.cop = new_state.cop
        
    def validate_state(self, state: LoadState) -> bool:
        """Validate simulation state"""
        return (state.power_consumption >= 0 and
                10 <= state.temperature <= 35 and
                15 <= state.setpoint <= 30 and
                1.5 <= state.cop <= 5.0)

class MotorSimulator(BaseSimulator):
    """Simulator for electric motors"""
    
    def __init__(self, model: Motor, config: Dict[str, Any]):
        super().__init__(model, config)
        self.efficiency_model = config.get('efficiency_model', 'advanced')
        self.thermal_model = config.get('thermal_model', True)
        self.market_enabled = config.get('market_enabled', False)
        self.dr_enabled = config.get('demand_response_enabled', True)
        
    def step(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        speed_request = inputs.get('speed_request', 0.0)
        load_factor = inputs.get('load_factor', 1.0)
        ambient_temp = inputs.get('ambient_temperature', 25.0)
        market_price = inputs.get('market_price', None)
        dr_signal = inputs.get('demand_response_signal', None)
        
        # Apply demand response if enabled
        if self.dr_enabled and dr_signal is not None:
            speed_request = self._apply_demand_response(speed_request, dr_signal)
            
        # Market optimization if enabled
        if self.market_enabled and market_price is not None:
            speed_request = self._optimize_market_position(speed_request, market_price)
        
        # Update motor state
        self.model.set_speed(speed_request)
        self.model.set_load_factor(load_factor)
        
        # Calculate efficiency and losses
        efficiency = self._calculate_efficiency(speed_request, load_factor)
        self.model.efficiency = efficiency
        
        # Apply thermal model if enabled
        if self.thermal_model:
            self._update_temperature(speed_request, load_factor, ambient_temp)
            
        # Calculate power consumption
        power = self._calculate_power_consumption(speed_request, load_factor, efficiency)
        self.model.current_power = power
        
        # Get and save state
        state = self.get_state()
        self.save_state(state.to_dict())
        
        return state.to_dict()
        
    def _calculate_efficiency(self, speed: float, load: float) -> float:
        """Advanced efficiency model based on speed and load"""
        if self.efficiency_model == 'advanced':
            speed_ratio = speed / self.model.rated_speed
            
            # Core losses (constant)
            core_loss = 0.02
            
            # Copper losses (load dependent)
            copper_loss = 0.03 * load * load
            
            # Friction losses (speed dependent)
            friction_loss = 0.01 * speed_ratio * speed_ratio
            
            # Stray losses
            stray_loss = 0.01 * load * speed_ratio
            
            total_losses = core_loss + copper_loss + friction_loss + stray_loss
            return max(0.1, 1 - total_losses)
        else:
            return 0.9  # Default efficiency
            
    def _calculate_power_consumption(
        self, speed: float, load: float, efficiency: float
    ) -> float:
        """Calculate power consumption"""
        speed_ratio = speed / self.model.rated_speed
        mechanical_power = self.model.rated_power * speed_ratio * load
        return mechanical_power / efficiency
        
    def _update_temperature(
        self, speed: float, load: float, ambient_temp: float
    ):
        """Thermal model for motor temperature"""
        # Calculate losses
        power = self._calculate_power_consumption(speed, load, self.model.efficiency)
        losses = power * (1 - self.model.efficiency)
        
        # Thermal resistance and capacity
        r_thermal = self.config.get('thermal_resistance', 0.05)  # K/W
        c_thermal = self.config.get('thermal_capacity', 5000)  # J/K
        
        # Temperature rise
        temp_rise = losses * r_thermal
        time_constant = r_thermal * c_thermal
        
        # Update temperature
        current_temp = self.model.get_temperature()
        delta_t = (ambient_temp + temp_rise - current_temp) * self.time_step / time_constant
        self.model.set_temperature(current_temp + delta_t)
        
    def _apply_demand_response(self, speed: float, dr_signal: Dict[str, Any]) -> float:
        """Apply demand response signal"""
        dr_type = dr_signal.get('type', 'none')
        dr_value = dr_signal.get('value', 0.0)
        
        if dr_type == 'curtailment':
            return speed * (1 - dr_value)
        return speed
        
    def _optimize_market_position(self, speed: float, market_price: float) -> float:
        """Optimize speed based on market price"""
        threshold_high = self.config.get('price_threshold_high', 100)
        
        if market_price > threshold_high:
            return speed * 0.8  # Reduce speed by 20%
        return speed

    def get_state(self) -> LoadState:
        """Get current simulation state"""
        return LoadState(
            component_type="motor",
            timestamp=datetime.now().timestamp(),
            power_consumption=self.model.current_power,
            speed=self.model.current_speed,
            temperature=self.model.get_temperature(),
            efficiency=self.model.efficiency
        )
        
    def update_state(self, new_state: LoadState) -> None:
        """Update simulation state"""
        self.model.current_power = new_state.power_consumption
        self.model.current_speed = new_state.speed
        self.model.set_temperature(new_state.temperature)
        self.model.efficiency = new_state.efficiency
        
    def validate_state(self, state: LoadState) -> bool:
        """Validate simulation state"""
        return (state.power_consumption >= 0 and
                0 <= state.speed <= self.model.rated_speed and
                0 <= state.temperature <= 150 and
                0.1 <= state.efficiency <= 1.0) 