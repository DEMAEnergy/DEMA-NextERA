from typing import Dict, Any, Optional
from .base_controller import BaseController
from .load_controller import HVACController, MotorController, DataCenterCoolingController
from .source_controller import PVController, WindTurbineController
from ..base_model import BaseModel

class ControllerFactory:
    """Factory for creating resource controllers"""
    
    _controller_types = {
        'hvac': HVACController,
        'motor': MotorController,
        'data_center_cooling': DataCenterCoolingController,
        'pv': PVController,
        'wind': WindTurbineController
    }
    
    @classmethod
    def create_controller(
        cls,
        resource_type: str,
        model: BaseModel,
        config: Dict[str, Any]
    ) -> BaseController:
        """Create a controller instance for the specified resource type"""
        
        if resource_type not in cls._controller_types:
            raise ValueError(f"Unknown resource type: {resource_type}")
            
        controller_class = cls._controller_types[resource_type]
        return controller_class(model, config)
    
    @classmethod
    def get_supported_types(cls) -> list:
        """Get list of supported resource types"""
        return list(cls._controller_types.keys()) 