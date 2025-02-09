from typing import Dict, Any, Optional
from .protocol_factory import ProtocolFactory
from .base_protocol import BaseProtocol
import asyncio
from datetime import datetime

class ResourceCommunicator:
    """Manages communication with resources using different protocols"""
    
    def __init__(self):
        self.resources: Dict[str, Dict[str, Any]] = {}
        self.protocols: Dict[str, BaseProtocol] = {}
        self.status_callbacks = {}
        
    async def add_resource(self, resource_id: str, protocol_type: str, config: Dict[str, Any]) -> bool:
        """Add a new resource with its communication protocol"""
        try:
            protocol = ProtocolFactory.create_protocol(
                protocol_type,
                f"{resource_id}_protocol",
                config
            )
            
            self.resources[resource_id] = {
                "protocol_type": protocol_type,
                "config": config,
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
            
    async def remove_resource(self, resource_id: str) -> bool:
        """Remove a resource and its protocol"""
        if resource_id in self.protocols:
            await self.protocols[resource_id].disconnect()
            del self.protocols[resource_id]
            del self.resources[resource_id]
            return True
        return False
    
    async def send_command(self, resource_id: str, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send command to a specific resource"""
        if resource_id not in self.protocols:
            return {"success": False, "error": "Resource not found"}
            
        protocol = self.protocols[resource_id]
        response = await protocol.send_command(command, params)
        
        if response["success"]:
            self.resources[resource_id]["last_command"] = {
                "command": command,
                "params": params,
                "timestamp": datetime.now()
            }
            
        return response
    
    async def get_resource_status(self, resource_id: str) -> Dict[str, Any]:
        """Get current status of a resource"""
        if resource_id not in self.protocols:
            return {"success": False, "error": "Resource not found"}
            
        protocol = self.protocols[resource_id]
        status = await protocol.read_status()
        
        if status["success"]:
            self.resources[resource_id]["last_status"] = status["data"]
            self.resources[resource_id]["last_update"] = datetime.now()
            
        return status
    
    async def subscribe_to_resource(self, resource_id: str, callback: callable) -> bool:
        """Subscribe to real-time updates from a resource"""
        if resource_id not in self.protocols:
            return False
            
        protocol = self.protocols[resource_id]
        self.status_callbacks[resource_id] = callback
        
        async def status_handler(data: Dict[str, Any]):
            self.resources[resource_id]["last_status"] = data
            self.resources[resource_id]["last_update"] = datetime.now()
            await callback(data)
        
        return await protocol.subscribe_to_updates(status_handler)
    
    def get_resource_info(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a resource"""
        return self.resources.get(resource_id)
    
    def get_all_resources(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all resources"""
        return self.resources
    
    async def reconnect_resource(self, resource_id: str) -> bool:
        """Reconnect to a resource"""
        if resource_id not in self.protocols:
            return False
            
        protocol = self.protocols[resource_id]
        await protocol.disconnect()
        return await protocol.connect()
    
    async def start_monitoring(self):
        """Start monitoring all resources"""
        while True:
            for resource_id, protocol in self.protocols.items():
                if protocol.status == "disconnected":
                    await self.reconnect_resource(resource_id)
            await asyncio.sleep(60)  # Check every minute 