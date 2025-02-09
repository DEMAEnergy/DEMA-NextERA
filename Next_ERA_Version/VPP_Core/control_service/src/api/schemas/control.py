from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime

class ControlSetpoint(BaseModel):
    """Represents a control setpoint received from dispatch service"""
    device_id: str = Field(..., description="Unique identifier of the device")
    setpoint_value: float = Field(..., description="Target value to be achieved")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    priority: int = Field(default=1, description="Priority level of the control action")

class ControlFeedback(BaseModel):
    """Represents feedback from the control implementation"""
    device_id: str
    actual_value: float
    setpoint_value: float
    error: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(..., description="Current status of control implementation")

class ControlAdjustment(BaseModel):
    """Represents a control adjustment calculation"""
    device_id: str
    adjustment_value: float
    error_metric: float
    confidence: float = Field(ge=0, le=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class BatchControlRequest(BaseModel):
    """Batch request for multiple control setpoints"""
    controls: List[ControlSetpoint]
    execution_priority: str = Field(default="sequential", description="parallel or sequential execution")

class ControlResponse(BaseModel):
    """Standard response format for control operations"""
    success: bool
    message: str
    data: Optional[Dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow) 