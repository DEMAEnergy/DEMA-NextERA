from typing import Dict, Any
from datetime import datetime, timedelta
from .base_simulator import BaseSimulator
from .state import StorageState
from ..Storage.battery import Battery
from ..Storage.thermal_storage import ThermalStorage

class BatterySimulator(BaseSimulator):
    """Simulator for battery storage systems"""
    
    def __init__(self, model: Battery, config: Dict[str, Any]):
        super().__init__(model, config)
        self.temperature_model = config.get('temperature_model', 'constant')
        self.degradation_model = config.get('degradation_model', 'linear')
        self.market_enabled = config.get('market_enabled', False)
        self.emergency_response_enabled = config.get('emergency_response_enabled', True)
        
    def step(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        power_request = inputs.get('power_request', 0)
        ambient_temp = inputs.get('ambient_temperature', 25.0)
        market_price = inputs.get('market_price', None)
        grid_frequency = inputs.get('grid_frequency', 50.0)
        duration = self.time_step / 3600  # convert to hours
        
        # Check for grid emergencies
        if self.emergency_response_enabled:
            if abs(grid_frequency - 50.0) > 0.5:
                self._handle_frequency_response(grid_frequency)
        
        # Market optimization if enabled
        if self.market_enabled and market_price is not None:
            power_request = self._optimize_market_position(power_request, market_price)
        
        # Simulate battery behavior
        if power_request > 0:
            success = self.model.charge(power_request, duration)
        else:
            success = self.model.discharge(abs(power_request), duration)
            
        # Simulate temperature effects
        if self.temperature_model == 'dynamic':
            self._simulate_temperature(power_request, ambient_temp)
            
        # Simulate degradation
        if self.degradation_model == 'linear':
            self._simulate_degradation(power_request, duration)
            
        # Get current state
        state = self.get_state()
        self.save_state(state.to_dict())
        
        return state.to_dict()
        
    def _simulate_temperature(self, power: float, ambient_temp: float):
        """Simulate battery temperature changes with thermal mass consideration"""
        power_loss = abs(power) * (1 - self.model.round_trip_efficiency)
        thermal_mass = self.config.get('thermal_mass', 100)  # J/K
        temp_rise = (power_loss * 0.1) / thermal_mass
        cooling_rate = self.config.get('cooling_rate', 0.05)
        current_temp = self.model.get_temperature()
        new_temp = current_temp + temp_rise - (current_temp - ambient_temp) * cooling_rate
        self.model.set_temperature(new_temp)
        
    def _simulate_degradation(self, power: float, duration: float):
        """Simulate battery degradation with multiple factors"""
        if abs(power) > 0:
            # Cycle degradation
            depth_of_discharge = abs(power) / self.model.capacity
            cycle_impact = depth_of_discharge * duration / 24
            
            # Temperature impact
            temp = self.model.get_temperature()
            temp_factor = 1.0 + max(0, (temp - 25) * 0.1)
            
            self.model.cycles_used += cycle_impact * temp_factor
            
    def _handle_frequency_response(self, grid_frequency: float):
        """Handle grid frequency deviations"""
        freq_deviation = grid_frequency - 50.0
        response_power = -freq_deviation * self.model.capacity * 0.2
        self.model.update_setpoint(response_power)
        
    def _optimize_market_position(self, power_request: float, market_price: float) -> float:
        """Optimize battery operation based on market price"""
        threshold_high = self.config.get('price_threshold_high', 100)
        threshold_low = self.config.get('price_threshold_low', 20)
        
        if market_price > threshold_high and self.model.get_available_capacity() > 0:
            return -self.model.capacity  # Discharge at max rate
        elif market_price < threshold_low and self.model.get_available_capacity() < self.model.capacity:
            return self.model.capacity  # Charge at max rate
        
        return power_request

    def get_state(self) -> StorageState:
        """Get current simulation state"""
        return StorageState(
            component_type="battery",
            timestamp=datetime.now().timestamp(),
            capacity=self.model.capacity,
            current_charge=self.model.get_current_charge(),
            charge_rate=self.model.get_charge_rate(),
            discharge_rate=self.model.get_discharge_rate()
        )
        
    def update_state(self, new_state: StorageState) -> None:
        """Update simulation state"""
        self.model.set_current_charge(new_state.current_charge)
        
    def validate_state(self, state: StorageState) -> bool:
        """Validate simulation state"""
        return (0 <= state.current_charge <= state.capacity and
                state.charge_rate >= 0 and
                state.discharge_rate >= 0)

class ThermalStorageSimulator(BaseSimulator):
    """Simulator for thermal storage systems"""
    
    def __init__(self, model: ThermalStorage, config: Dict[str, Any]):
        super().__init__(model, config)
        self.heat_loss_model = config.get('heat_loss_model', 'linear')
        self.market_enabled = config.get('market_enabled', False)
        self.emergency_response_enabled = config.get('emergency_response_enabled', True)
        
    def step(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        power_request = inputs.get('power_request', 0)
        ambient_temp = inputs.get('ambient_temperature', 20.0)
        market_price = inputs.get('market_price', None)
        grid_frequency = inputs.get('grid_frequency', 50.0)
        duration = self.time_step / 3600
        
        # Check for grid emergencies
        if self.emergency_response_enabled:
            if abs(grid_frequency - 50.0) > 0.5:
                self._handle_frequency_response(grid_frequency)
        
        # Market optimization if enabled
        if self.market_enabled and market_price is not None:
            power_request = self._optimize_market_position(power_request, market_price)
        
        # Update ambient temperature
        self.model.ambient_temperature = ambient_temp
        
        # Simulate thermal losses
        if self.heat_loss_model == 'linear':
            self._simulate_heat_loss(duration)
            
        # Simulate charging/discharging
        if power_request > 0:
            success = self.model.charge(power_request, duration)
        else:
            success = self.model.discharge(abs(power_request), duration)
            
        # Get current state
        state = self.get_state()
        self.save_state(state.to_dict())
        
        return state.to_dict()
        
    def _simulate_heat_loss(self, duration: float):
        """Simulate thermal losses to environment with advanced modeling"""
        # Calculate conductive losses through insulation
        temp_diff = self.model.current_temperature - self.model.ambient_temperature
        surface_area = self.config.get('surface_area', 10.0)  # m²
        insulation_thickness = self.config.get('insulation_thickness', 0.1)  # m
        thermal_conductivity = self.config.get('thermal_conductivity', 0.04)  # W/m·K
        
        conductive_loss = (
            thermal_conductivity * surface_area * temp_diff * duration / 
            insulation_thickness
        )
        
        # Calculate convective losses
        convection_coefficient = self.config.get('convection_coefficient', 5.0)  # W/m²·K
        convective_loss = convection_coefficient * surface_area * temp_diff * duration
        
        # Total losses
        total_losses = (conductive_loss + convective_loss) / 3600  # Convert to kWh
        temp_drop = self.model.calculate_temperature_change(total_losses)
        self.model.current_temperature -= temp_drop

    def _handle_frequency_response(self, grid_frequency: float):
        """Handle grid frequency deviations"""
        freq_deviation = grid_frequency - 50.0
        response_power = -freq_deviation * self.model.capacity * 0.15  # Slower response than batteries
        self.model.update_setpoint(response_power)
        
    def _optimize_market_position(self, power_request: float, market_price: float) -> float:
        """Optimize thermal storage operation based on market price"""
        threshold_high = self.config.get('price_threshold_high', 100)
        threshold_low = self.config.get('price_threshold_low', 20)
        
        # Consider temperature constraints
        max_temp = self.config.get('max_temperature', 95.0)
        min_temp = self.config.get('min_temperature', 60.0)
        
        if market_price > threshold_high and self.model.current_temperature > min_temp:
            return -self.model.capacity  # Discharge at max rate
        elif market_price < threshold_low and self.model.current_temperature < max_temp:
            return self.model.capacity  # Charge at max rate
        
        return power_request

    def get_state(self) -> StorageState:
        """Get current simulation state"""
        return StorageState(
            component_type="thermal_storage",
            timestamp=datetime.now().timestamp(),
            capacity=self.model.capacity,
            current_charge=self.model.get_thermal_energy(),
            charge_rate=self.model.get_charge_rate(),
            discharge_rate=self.model.get_discharge_rate()
        )
        
    def update_state(self, new_state: StorageState) -> None:
        """Update simulation state"""
        self.model.set_thermal_energy(new_state.current_charge)
        
    def validate_state(self, state: StorageState) -> bool:
        """Validate simulation state"""
        min_temp = self.config.get('min_temperature', 60.0)
        max_temp = self.config.get('max_temperature', 95.0)
        current_temp = self.model.current_temperature
        
        return (0 <= state.current_charge <= state.capacity and
                state.charge_rate >= 0 and
                state.discharge_rate >= 0 and
                min_temp <= current_temp <= max_temp) 