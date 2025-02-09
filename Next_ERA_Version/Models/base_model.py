from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

class ResourceStatus(Enum):
    IDLE = "idle"
    ACTIVE = "active"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"

class BaseModel(ABC):
    """Base class for all VPP resource models"""
    
    def __init__(self, resource_id: str, capacity: float, location: Dict[str, float]):
        self.resource_id = resource_id
        self.capacity = capacity  # in kW or kWh depending on resource type
        self.location = location  # {latitude: float, longitude: float}
        self.status = ResourceStatus.IDLE
        self.last_updated = datetime.now()
        self.power_setpoint = 0.0
        self.availability = 1.0
        self.maintenance_schedule = []
        self.performance_metrics = {
            'efficiency': 1.0,
            'response_time': 0.0,
            'availability': 1.0
        }
    
    @abstractmethod
    def start(self) -> bool:
        """Start the resource"""
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """Stop the resource"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the resource"""
        pass
    
    @abstractmethod
    def update_setpoint(self, value: float) -> bool:
        """Update the setpoint of the resource"""
        pass

    @abstractmethod
    def get_available_capacity(self) -> float:
        """Get currently available capacity"""
        pass

    @abstractmethod
    def handle_emergency(self, emergency_type: str) -> bool:
        """Handle emergency situations"""
        pass

    def update_metrics(self, metrics: Dict[str, float]) -> None:
        """Update performance metrics"""
        self.performance_metrics.update(metrics)
        self.last_updated = datetime.now()

    def schedule_maintenance(self, schedule: list) -> None:
        """Schedule maintenance windows"""
        self.maintenance_schedule = schedule

    def is_available(self) -> bool:
        """Check if resource is available for dispatch"""
        return (self.status == ResourceStatus.IDLE or 
                self.status == ResourceStatus.ACTIVE) and self.availability > 0 