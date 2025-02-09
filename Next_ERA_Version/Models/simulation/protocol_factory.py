from typing import Dict, Any, Optional, Union
from ..communication.protocol_factory import ProtocolFactory
from ..communication.base_protocol import BaseProtocol
from .protocol_simulator import SimulatedProtocolAdapter
from .base_simulator import BaseSimulator
from .storage_simulator import BatterySimulator, ThermalStorageSimulator
from .source_simulator import PVSimulator, WindTurbineSimulator
from .load_simulator import HVACSimulator, MotorSimulator
from .data_center_cooling import DataCenterCooling
from .cooling_simulator import DataCenterCoolingSimulator

class SimulationProtocolFactory:
    """Factory for creating real or simulated protocol instances"""
    
    _simulator_types = {
        'battery': BatterySimulator,
        'thermal_storage': ThermalStorageSimulator,
        'pv': PVSimulator,
        'wind': WindTurbineSimulator,
        'hvac': HVACSimulator,
        'motor': MotorSimulator,
        'data_center_cooling': DataCenterCoolingSimulator,
    }
    
    @classmethod
    def create_protocol(
        cls,
        resource_type: str,
        protocol_type: str,
        protocol_id: str,
        config: Dict[str, Any],
        simulation_mode: bool = False,
        model: Optional[Any] = None
    ) -> BaseProtocol:
        """Create either a real or simulated protocol instance"""
        
        if simulation_mode:
            if resource_type not in cls._simulator_types:
                raise ValueError(f"Unknown simulator type: {resource_type}")
                
            # Create simulator instance
            simulator_class = cls._simulator_types[resource_type]
            simulator = simulator_class(model, config.get('simulator_config', {}))
            
            # Create simulator protocol adapter
            return SimulatedProtocolAdapter(simulator, protocol_id, config)
        else:
            # Create real protocol instance
            return ProtocolFactory.create_protocol(protocol_type, protocol_id, config) 