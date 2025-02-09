from typing import Dict, Any
from datetime import datetime
from .base_simulator import BaseSimulator
from .state import SourceState
from ..Source.pv_system import PVSystem
from ..Source.wind_turbine import WindTurbine
import numpy as np

class PVSimulator(BaseSimulator):
    """Simulator for PV systems"""
    
    def __init__(self, model: PVSystem, config: Dict[str, Any]):
        super().__init__(model, config)
        self.cloud_impact = config.get('cloud_impact', True)
        self.temperature_model = config.get('temperature_model', 'advanced')
        self.inverter_model = config.get('inverter_model', 'dynamic')
        self.market_enabled = config.get('market_enabled', False)
        
    def step(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        irradiance = inputs.get('irradiance', 0.0)
        ambient_temp = inputs.get('ambient_temperature', 25.0)
        cloud_cover = inputs.get('cloud_cover', 0.0)
        market_price = inputs.get('market_price', None)
        wind_speed = inputs.get('wind_speed', 0.0)  # For cooling effect
        
        # Apply cloud cover impact with advanced modeling
        if self.cloud_impact:
            irradiance = self._apply_cloud_model(irradiance, cloud_cover)
            
        # Calculate panel temperature
        panel_temp = self._calculate_panel_temperature(
            ambient_temp, irradiance, wind_speed
        )
        
        # Calculate DC power output
        dc_power = self._calculate_dc_power(irradiance, panel_temp)
        
        # Apply inverter efficiency
        ac_power = self._apply_inverter_model(dc_power)
        
        # Market optimization if enabled
        if self.market_enabled and market_price is not None:
            ac_power = self._optimize_market_position(ac_power, market_price)
        
        # Update model
        self.model.update_power_output(ac_power)
        
        # Get and save state
        state = self.get_state()
        self.save_state(state.to_dict())
        
        return state.to_dict()
        
    def _apply_cloud_model(self, irradiance: float, cloud_cover: float) -> float:
        """Advanced cloud impact modeling"""
        # Different cloud types have different impacts
        cloud_factors = {
            'thin': 0.8,
            'medium': 0.5,
            'thick': 0.2
        }
        # Assume cloud thickness based on cover amount
        if cloud_cover < 0.3:
            factor = cloud_factors['thin']
        elif cloud_cover < 0.7:
            factor = cloud_factors['medium']
        else:
            factor = cloud_factors['thick']
            
        return irradiance * (1 - cloud_cover * factor)
        
    def _calculate_panel_temperature(
        self, ambient_temp: float, irradiance: float, wind_speed: float
    ) -> float:
        """Calculate panel temperature using advanced thermal model"""
        # NOCT method with wind correction
        noct = self.config.get('noct', 45.0)
        temp_coeff = self.config.get('temp_coefficient', 0.04)
        wind_factor = max(0.5, min(1.0, 1 - wind_speed * 0.05))
        
        delta_t = (noct - 20) * (irradiance / 800) * wind_factor
        return ambient_temp + delta_t
        
    def _calculate_dc_power(self, irradiance: float, panel_temp: float) -> float:
        """Calculate DC power output with temperature effects"""
        nominal_power = self.model.capacity
        temp_coeff = self.config.get('temp_coefficient', -0.004)  # %/°C
        ref_temp = 25.0
        
        # Temperature effect
        temp_factor = 1 + temp_coeff * (panel_temp - ref_temp)
        
        # Irradiance effect with non-linear low-light efficiency
        if irradiance < 200:
            irr_factor = (irradiance / 1000) * 0.9  # Reduced efficiency at low light
        else:
            irr_factor = irradiance / 1000
            
        return nominal_power * temp_factor * irr_factor
        
    def _apply_inverter_model(self, dc_power: float) -> float:
        """Dynamic inverter efficiency model"""
        if self.inverter_model == 'dynamic':
            nominal_power = self.model.capacity
            load_ratio = dc_power / nominal_power
            
            if load_ratio < 0.1:
                efficiency = 0.86  # Low load efficiency
            elif load_ratio < 0.2:
                efficiency = 0.90
            elif load_ratio < 0.5:
                efficiency = 0.95
            else:
                efficiency = 0.97  # Peak efficiency
        else:
            efficiency = 0.95  # Simple constant model
            
        return dc_power * efficiency
        
    def _optimize_market_position(self, power: float, market_price: float) -> float:
        """Optimize output based on market conditions"""
        # For PV, we can only curtail output
        threshold_low = self.config.get('price_threshold_low', 0.0)
        
        if market_price < threshold_low:
            return power * 0.5  # Curtail to 50%
        return power

    def get_state(self) -> SourceState:
        """Get current simulation state"""
        return SourceState(
            component_type="pv_system",
            timestamp=datetime.now().timestamp(),
            max_power_output=self.model.capacity,
            current_output=self.model.current_output,
            availability=self.model.availability
        )
        
    def update_state(self, new_state: SourceState) -> None:
        """Update simulation state"""
        self.model.current_output = new_state.current_output
        self.model.availability = new_state.availability
        
    def validate_state(self, state: SourceState) -> bool:
        """Validate simulation state"""
        return (0 <= state.current_output <= state.max_power_output and
                0 <= state.availability <= 1.0)

class WindTurbineSimulator(BaseSimulator):
    """Simulator for wind turbines"""
    
    def __init__(self, model: WindTurbine, config: Dict[str, Any]):
        super().__init__(model, config)
        self.turbulence_model = config.get('turbulence_model', 'advanced')
        self.wake_model = config.get('wake_model', True)
        self.market_enabled = config.get('market_enabled', False)
        
    def step(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        wind_speed = inputs.get('wind_speed', 0.0)
        air_density = inputs.get('air_density', 1.225)
        turbulence = inputs.get('turbulence', 0.1)
        wind_direction = inputs.get('wind_direction', 0.0)
        market_price = inputs.get('market_price', None)
        nearby_turbines = inputs.get('nearby_turbines', [])
        
        # Apply turbulence effects
        if self.turbulence_model == 'advanced':
            wind_speed = self._apply_turbulence_model(wind_speed, turbulence)
            
        # Apply wake effects if enabled
        if self.wake_model and nearby_turbines:
            wind_speed = self._apply_wake_model(
                wind_speed, wind_direction, nearby_turbines
            )
            
        # Calculate power output with air density correction
        power = self._calculate_power_output(wind_speed, air_density)
        
        # Market optimization if enabled
        if self.market_enabled and market_price is not None:
            power = self._optimize_market_position(power, market_price)
        
        # Update model
        self.model.update_power_output(power)
        
        # Get and save state
        state = self.get_state()
        self.save_state(state.to_dict())
        
        return state.to_dict()
        
    def _apply_turbulence_model(self, wind_speed: float, turbulence: float) -> float:
        """Advanced turbulence modeling using von Karman spectrum"""
        if turbulence <= 0:
            return wind_speed
            
        # Generate turbulent fluctuations
        mean_freq = 0.1  # Hz
        time_step = self.time_step
        spectrum_intensity = turbulence * wind_speed
        
        fluctuation = spectrum_intensity * np.random.normal(0, 1)
        return wind_speed + fluctuation
        
    def _apply_wake_model(
        self, wind_speed: float, wind_direction: float, nearby_turbines: list
    ) -> float:
        """Apply wake effects from nearby turbines"""
        wake_factor = 1.0
        
        for turbine in nearby_turbines:
            distance = turbine.get('distance', 0)
            direction = turbine.get('direction', 0)
            diameter = turbine.get('diameter', 100)
            
            # Check if turbine is upstream
            angle_diff = abs(wind_direction - direction)
            if angle_diff < 30 and distance > 0:  # Within 30 degrees
                # Jensen wake model
                wake_decay = 0.075
                radius = diameter/2 + wake_decay * distance
                wake_deficit = (1 - np.sqrt(1 - 0.9)) * (diameter/(2*radius))**2
                wake_factor *= (1 - wake_deficit)
        
        return wind_speed * wake_factor
        
    def _calculate_power_output(self, wind_speed: float, air_density: float) -> float:
        """Calculate power output with air density correction"""
        # Get power curve value
        base_power = self.model.get_power_curve_value(wind_speed)
        
        # Apply air density correction
        rho_0 = 1.225  # Reference air density
        density_factor = air_density / rho_0
        
        return base_power * density_factor
        
    def _optimize_market_position(self, power: float, market_price: float) -> float:
        """Optimize output based on market conditions"""
        threshold_low = self.config.get('price_threshold_low', 0.0)
        
        if market_price < threshold_low:
            return power * 0.6  # Curtail to 60%
        return power

    def get_state(self) -> SourceState:
        """Get current simulation state"""
        return SourceState(
            component_type="wind_turbine",
            timestamp=datetime.now().timestamp(),
            max_power_output=self.model.capacity,
            current_output=self.model.current_output,
            availability=self.model.availability
        )
        
    def update_state(self, new_state: SourceState) -> None:
        """Update simulation state"""
        self.model.current_output = new_state.current_output
        self.model.availability = new_state.availability
        
    def validate_state(self, state: SourceState) -> bool:
        """Validate simulation state"""
        return (0 <= state.current_output <= state.max_power_output and
                0 <= state.availability <= 1.0)

class SourceSimulator:
    def __init__(self, max_power_output):
        self.max_power_output = max_power_output
        self.current_output = 0
        self.availability = 1.0  # 0-1 scale
    
    def get_state(self):
        return {
            'max_power_output': self.max_power_output,
            'current_output': self.current_output,
            'availability': self.availability
        }
    
    def update_state(self, new_state):
        self.current_output = new_state['current_output']
        self.availability = new_state['availability'] 