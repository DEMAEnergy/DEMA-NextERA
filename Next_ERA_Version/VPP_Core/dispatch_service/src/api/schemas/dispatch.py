from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
from ...core.models.optimization import (
    ResourceState,
    MarketSignal,
    DispatchSchedule
)

class CreateScheduleRequest(BaseModel):
    """Request to create a new dispatch schedule"""
    resources: List[ResourceState]
    market_signals: List[MarketSignal]
    start_time: datetime
    end_time: datetime
    optimization_params: Optional[Dict[str, any]] = None

class UpdateScheduleRequest(BaseModel):
    """Request to update an existing schedule"""
    resources: Optional[List[ResourceState]] = None
    market_signals: Optional[List[MarketSignal]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    optimization_params: Optional[Dict[str, any]] = None

class ScheduleMetrics(BaseModel):
    """Performance metrics for a schedule"""
    total_energy_mwh: float
    total_cost: float
    total_revenue: float
    profit: float
    average_power: float

class ScheduleStatus(BaseModel):
    """Current status of a schedule"""
    schedule_id: str
    status: str  # created, executing, completed, failed, stopped
    current_interval: Optional[datetime] = None
    progress_percent: float
    last_update: datetime
    error_message: Optional[str] = None
    performance_metrics: Optional[ScheduleMetrics] = None

class ScheduleResponse(BaseModel):
    """Response containing schedule information"""
    schedule_id: str
    status: str
    schedule: DispatchSchedule
    metrics: ScheduleMetrics

class ExecutionCommand(BaseModel):
    """Command to control schedule execution"""
    command: str  # execute, stop, pause, resume
    schedule_id: str
    timestamp: datetime
    parameters: Optional[Dict[str, any]] = None 