from typing import Dict, Any, Optional, Type
from datetime import datetime
from .base_protocol import BaseProtocol
from .protocols.modbus_protocol import ModbusProtocol
from .protocols.mqtt_protocol import MQTTProtocol
from ..simulation.protocol_simulator import SimulatedProtocolAdapter

class ProtocolType:
    """Enumeration of supported protocol types"""
    MODBUS = "modbus"
    MQTT = "mqtt"
    SIMULATED = "simulated"

class ProtocolFactory:
    """Factory class for creating communication protocol instances"""
    
    _protocols: Dict[str, Type[BaseProtocol]] = {
        ProtocolType.MODBUS: ModbusProtocol,
        ProtocolType.MQTT: MQTTProtocol,
        ProtocolType.SIMULATED: SimulatedProtocolAdapter
    }
    
    _protocol_configs: Dict[str, Dict[str, Any]] = {
        ProtocolType.MODBUS: {
            'required_params': ['host', 'port', 'unit_id'],
            'optional_params': {
                'timeout': 1.0,
                'retries': 3,
                'baudrate': 9600
            }
        },
        ProtocolType.MQTT: {
            'required_params': ['broker', 'port', 'topic'],
            'optional_params': {
                'qos': 1,
                'keepalive': 60,
                'username': None,
                'password': None
            }
        },
        ProtocolType.SIMULATED: {
            'required_params': ['simulator'],
            'optional_params': {
                'latency': 50,
                'packet_loss': 0.001,
                'bandwidth': 1000
            }
        }
    }
    
    _protocol_instances: Dict[str, BaseProtocol] = {}
    _last_validation: Dict[str, datetime] = {}
    
    @classmethod
    def register_protocol(
        cls, protocol_type: str, protocol_class: Type[BaseProtocol],
        config_template: Dict[str, Any]
    ) -> None:
        """Register a new protocol type with configuration template"""
        if not issubclass(protocol_class, BaseProtocol):
            raise ValueError("Protocol class must inherit from BaseProtocol")
            
        if 'required_params' not in config_template or 'optional_params' not in config_template:
            raise ValueError("Config template must specify required and optional parameters")
            
        cls._protocols[protocol_type] = protocol_class
        cls._protocol_configs[protocol_type] = config_template
        
    @classmethod
    def create_protocol(
        cls, protocol_type: str, protocol_id: str, config: Dict[str, Any],
        simulation_mode: bool = False, model: Optional[Any] = None
    ) -> BaseProtocol:
        """Create a protocol instance with validation"""
        # Check protocol type
        if protocol_type not in cls._protocols:
            raise ValueError(f"Unknown protocol type: {protocol_type}")
            
        # Get protocol configuration template
        protocol_config = cls._protocol_configs[protocol_type]
        
        # Validate required parameters
        missing_params = [
            param for param in protocol_config['required_params']
            if param not in config
        ]
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
            
        # Add default values for optional parameters
        for param, default in protocol_config['optional_params'].items():
            if param not in config:
                config[param] = default
                
        # Create protocol instance
        if simulation_mode:
            protocol_class = cls._protocols[ProtocolType.SIMULATED]
            instance = protocol_class(model, protocol_id, config)
        else:
            protocol_class = cls._protocols[protocol_type]
            instance = protocol_class(protocol_id, config)
            
        # Store instance
        cls._protocol_instances[protocol_id] = instance
        cls._last_validation[protocol_id] = datetime.now()
        
        return instance
        
    @classmethod
    def get_protocol(cls, protocol_id: str) -> Optional[BaseProtocol]:
        """Get existing protocol instance"""
        return cls._protocol_instances.get(protocol_id)
        
    @classmethod
    def validate_protocol(cls, protocol_id: str) -> bool:
        """Validate protocol instance"""
        instance = cls._protocol_instances.get(protocol_id)
        if not instance:
            return False
            
        # Check last validation time
        last_validation = cls._last_validation.get(protocol_id, datetime.min)
        if (datetime.now() - last_validation).total_seconds() > 3600:  # Validate hourly
            try:
                if not instance.validate():
                    return False
                cls._last_validation[protocol_id] = datetime.now()
            except Exception:
                return False
                
        return True
        
    @classmethod
    def get_supported_protocols(cls) -> Dict[str, Dict[str, Any]]:
        """Get list of supported protocols with their configurations"""
        return {
            protocol_type: {
                'class': protocol_class.__name__,
                'config': cls._protocol_configs[protocol_type]
            }
            for protocol_type, protocol_class in cls._protocols.items()
        }
        
    @classmethod
    def cleanup(cls) -> None:
        """Clean up protocol instances"""
        for protocol in cls._protocol_instances.values():
            try:
                protocol.disconnect()
            except Exception:
                pass
        cls._protocol_instances.clear()
        cls._last_validation.clear() 