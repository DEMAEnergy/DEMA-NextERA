from datetime import datetime
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

class ResourceType(str, Enum):
    """Types of VPP resources"""
    BATTERY = "battery"
    SOLAR = "solar"
    WIND = "wind"
    DEMAND_RESPONSE = "demand_response"
    CHP = "chp"
    EV_CHARGER = "ev_charger"

class GridService(str, Enum):
    """Types of grid services"""
    ENERGY_ARBITRAGE = "energy_arbitrage"
    FREQUENCY_REGULATION = "frequency_regulation"
    VOLTAGE_SUPPORT = "voltage_support"
    PEAK_SHAVING = "peak_shaving"
    SPINNING_RESERVE = "spinning_reserve"

class ResourceConstraint(BaseModel):
    """Resource operational constraints"""
    min_power: float = Field(..., description="Minimum power output/consumption")
    max_power: float = Field(..., description="Maximum power output/consumption")
    ramp_up_rate: float = Field(..., description="Maximum power increase per minute")
    ramp_down_rate: float = Field(..., description="Maximum power decrease per minute")
    min_runtime: int = Field(0, description="Minimum runtime in minutes")
    min_downtime: int = Field(0, description="Minimum downtime in minutes")
    efficiency: float = Field(1.0, description="Resource efficiency factor")
    response_time: int = Field(0, description="Response time in seconds")
    min_soc: Optional[float] = Field(None, description="Minimum state of charge for storage")
    max_soc: Optional[float] = Field(None, description="Maximum state of charge for storage")
    cycle_cost: Optional[float] = Field(None, description="Cost per cycle for storage")
    maintenance_window: Optional[List[Dict[str, datetime]]] = Field(None, description="Scheduled maintenance windows")
    grid_connection_limit: Optional[float] = Field(None, description="Grid connection power limit")

    @validator('efficiency')
    def efficiency_must_be_positive(cls, v):
        if v <= 0 or v > 1:
            raise ValueError('Efficiency must be between 0 and 1')
        return v

class ResourceState(BaseModel):
    """Current state of a resource"""
    resource_id: str
    resource_type: ResourceType
    current_power: float
    state_of_charge: Optional[float] = None
    is_available: bool
    last_state_change: datetime
    constraints: ResourceConstraint
    forecast: Dict[str, float] = Field(default_factory=dict)
    temperature: Optional[float] = None
    health_status: Optional[str] = None
    maintenance_mode: bool = False
    grid_services_enabled: List[GridService] = Field(default_factory=list)
    location: Dict[str, float]  # latitude, longitude
    weather_dependent: bool = False
    weather_forecast: Optional[Dict[str, Any]] = None

class MarketSignal(BaseModel):
    """Market price and demand signals"""
    timestamp: datetime
    price: float
    demand: float
    frequency: Optional[float] = None
    voltage: Optional[float] = None
    grid_service_prices: Dict[GridService, float] = Field(default_factory=dict)
    location: Optional[Dict[str, float]] = None
    confidence_level: float = Field(1.0, ge=0, le=1)
    source: str = "market"

class OptimizationObjective(BaseModel):
    """Optimization objective configuration"""
    revenue_weight: float = Field(1.0, ge=0, le=1)
    grid_support_weight: float = Field(0.0, ge=0, le=1)
    environmental_weight: float = Field(0.0, ge=0, le=1)
    battery_degradation_weight: float = Field(0.0, ge=0, le=1)

class OptimizationResult(BaseModel):
    """Result of optimization calculation"""
    resource_id: str
    target_power: float
    start_time: datetime
    end_time: datetime
    expected_cost: float
    expected_revenue: float
    grid_service_contribution: Dict[GridService, float] = Field(default_factory=dict)
    constraints_violated: List[str] = Field(default_factory=list)
    confidence_level: float = Field(1.0, ge=0, le=1)
    expected_soc: Optional[float] = None
    carbon_impact: Optional[float] = None
    risk_level: str = "low"

class DispatchSchedule(BaseModel):
    """Complete dispatch schedule for all resources"""
    schedule_id: str
    start_time: datetime
    end_time: datetime
    interval_minutes: int
    resources: Dict[str, List[OptimizationResult]]
    total_cost: float
    total_revenue: float
    market_conditions: List[MarketSignal]
    grid_services_provided: Dict[GridService, float] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "draft"  # draft, confirmed, executing, completed, failed
    optimization_objective: OptimizationObjective
    risk_metrics: Dict[str, float] = Field(default_factory=dict)
    carbon_savings: float = 0.0

    def validate_schedule(self) -> bool:
        """Validate the complete schedule"""
        try:
            # Check time continuity
            for resource_id, schedule in self.resources.items():
                for i in range(len(schedule) - 1):
                    if schedule[i].end_time != schedule[i + 1].start_time:
                        return False
                    
                # Check constraint violations
                if any(len(result.constraints_violated) > 0 for result in schedule):
                    return False
                    
            # Validate total grid services don't exceed capacity
            for service, amount in self.grid_services_provided.items():
                if amount < 0:
                    return False
                    
            return True
        except Exception:
            return False

    def calculate_metrics(self) -> Dict[str, float]:
        """Calculate schedule performance metrics"""
        total_energy = sum(
            result.target_power * 
            (result.end_time - result.start_time).total_seconds() / 3600
            for schedule in self.resources.values()
            for result in schedule
        )
        
        return {
            "total_energy_mwh": total_energy,
            "total_cost": self.total_cost,
            "total_revenue": self.total_revenue,
            "profit": self.total_revenue - self.total_cost,
            "average_power": total_energy / (
                (self.end_time - self.start_time).total_seconds() / 3600
            ) if total_energy > 0 else 0,
            "carbon_savings": self.carbon_savings,
            "grid_services_revenue": sum(self.grid_services_provided.values()),
            "risk_adjusted_profit": self.total_revenue - self.total_cost - sum(
                self.risk_metrics.values()
            )
        } 