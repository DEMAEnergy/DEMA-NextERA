from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class ForecastType(str, Enum):
    LOAD = "load"
    RENEWABLE = "renewable"
    CONTROLLABILITY = "controllability"

class ForecastPoint(BaseModel):
    timestamp: datetime
    value: float
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None
    metadata: Dict = Field(default_factory=dict)

class ForecastSeries(BaseModel):
    forecast_type: ForecastType
    start_time: datetime
    end_time: datetime
    resolution: str  # e.g., "15min", "1h"
    points: List[ForecastPoint]
    model_info: Dict = Field(default_factory=dict)
    metadata: Dict = Field(default_factory=dict)

class LoadForecast(ForecastSeries):
    forecast_type: ForecastType = ForecastType.LOAD
    unit: str = "kW"
    location_id: Optional[str] = None
    customer_segment: Optional[str] = None

class RenewableForecast(ForecastSeries):
    forecast_type: ForecastType = ForecastType.RENEWABLE
    unit: str = "kW"
    source_type: str  # e.g., "solar", "wind"
    location_id: Optional[str] = None
    capacity: Optional[float] = None

class ControllabilityForecast(ForecastSeries):
    forecast_type: ForecastType = ForecastType.CONTROLLABILITY
    unit: str = "kW"
    resource_id: str
    min_power: List[float]
    max_power: List[float]
    response_time: Optional[float] = None  # in seconds
    cost_function: Optional[Dict] = None

class ForecastRequest(BaseModel):
    forecast_type: ForecastType
    start_time: datetime
    end_time: datetime
    resolution: str
    parameters: Dict = Field(default_factory=dict)

class ForecastResponse(BaseModel):
    request_id: str
    forecast: ForecastSeries
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "success"
    message: Optional[str] = None 