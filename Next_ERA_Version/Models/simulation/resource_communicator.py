from typing import Dict, Any, Optional
from ..communication.resource_communicator import ResourceCommunicator
from .protocol_factory import SimulationProtocolFactory

class SimulationAwareResourceCommunicator(ResourceCommunicator):
    """Resource communicator that can handle both real and simulated devices"""
    
    def __init__(self):
        super().__init__()
        self.simulation_mode = False
        
    async def add_resource(
        self,
        resource_id: str,
        resource_type: str,
        protocol_type: str,
        config: Dict[str, Any],
        model: Optional[Any] = None,
        simulation_mode: Optional[bool] = None
    ) -> bool:
        """Add a new resource with optional simulation support"""
        try:
            # Use instance or global simulation mode
            use_simulation = simulation_mode if simulation_mode is not None else self.simulation_mode
            
            protocol = SimulationProtocolFactory.create_protocol(
                resource_type=resource_type,
                protocol_type=protocol_type,
                protocol_id=f"{resource_id}_protocol",
                config=config,
                simulation_mode=use_simulation,
                model=model
            )
            
            self.resources[resource_id] = {
                "resource_type": resource_type,
                "protocol_type": protocol_type,
                "config": config,
                "simulation_mode": use_simulation,
                "last_status": None,
                "status": "initializing"
            }
            
            self.protocols[resource_id] = protocol
            
            # Initialize connection
            if await protocol.connect():
                self.resources[resource_id]["status"] = "connected"
                return True
            return False
            
        except Exception as e:
            print(f"Error adding resource {resource_id}: {str(e)}")
            return False
    
    def set_simulation_mode(self, enabled: bool):
        """Enable or disable simulation mode globally"""
        self.simulation_mode = enabled 