from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import numpy as np
from pulp import *
from scipy.optimize import minimize
import pandas as pd
from ..models.optimization import (
    ResourceState,
    MarketSignal,
    OptimizationResult,
    DispatchSchedule,
    GridService,
    OptimizationObjective,
    ResourceType
)

class DispatchOptimizer:
    """Service for calculating optimal dispatch schedules"""
    
    def __init__(self, config: Dict[str, any], simulator: Optional['VPPSimulator'] = None):
        self.config = config
        self.optimization_horizon = timedelta(hours=config.get('optimization_horizon_hours', 24))
        self.interval_minutes = config.get('interval_minutes', 15)
        self.risk_tolerance = config.get('risk_tolerance', 0.95)
        self.carbon_price = config.get('carbon_price', 0.0)
        self.grid_service_requirements = config.get('grid_service_requirements', {})
        self.simulator = simulator
        
    async def create_dispatch_schedule(
        self,
        resources: List[ResourceState],
        market_signals: List[MarketSignal],
        start_time: datetime,
        end_time: datetime,
        optimization_objective: Optional[OptimizationObjective] = None
    ) -> DispatchSchedule:
        """Create optimal dispatch schedule for given resources and market conditions"""
        
        # Use default optimization objective if none provided
        if optimization_objective is None:
            optimization_objective = OptimizationObjective()
        
        # Initialize schedule
        schedule_id = f"schedule_{datetime.utcnow().timestamp()}"
        schedule = DispatchSchedule(
            schedule_id=schedule_id,
            start_time=start_time,
            end_time=end_time,
            interval_minutes=self.interval_minutes,
            resources={},
            total_cost=0.0,
            total_revenue=0.0,
            market_conditions=market_signals,
            optimization_objective=optimization_objective
        )
        
        try:
            # Group resources by type for coordinated optimization
            resource_groups = self._group_resources(resources)
            
            # Calculate intervals
            intervals = self._calculate_intervals(start_time, end_time)
            
            # Perform multi-interval optimization for each resource group
            for resource_type, group_resources in resource_groups.items():
                group_schedule = self._optimize_resource_group(
                    resource_type=resource_type,
                    resources=group_resources,
                    market_signals=market_signals,
                    intervals=intervals,
                    optimization_objective=optimization_objective
                )
                
                # Add group results to schedule
                for resource_id, resource_schedule in group_schedule.items():
                    schedule.resources[resource_id] = resource_schedule
                    schedule.total_cost += sum(result.expected_cost for result in resource_schedule)
                    schedule.total_revenue += sum(result.expected_revenue for result in resource_schedule)
                    
                    # Aggregate grid services
                    for result in resource_schedule:
                        for service, amount in result.grid_service_contribution.items():
                            schedule.grid_services_provided[service] = (
                                schedule.grid_services_provided.get(service, 0) + amount
                            )
            
            # Calculate risk metrics
            schedule.risk_metrics = self._calculate_risk_metrics(schedule)
            
            # Calculate carbon impact
            schedule.carbon_savings = self._calculate_carbon_savings(schedule)
            
            return schedule
            
        except Exception as e:
            raise ValueError(f"Optimization failed: {str(e)}")
    
    def _group_resources(self, resources: List[ResourceState]) -> Dict[ResourceType, List[ResourceState]]:
        """Group resources by type for coordinated optimization"""
        groups = {}
        for resource in resources:
            if resource.resource_type not in groups:
                groups[resource.resource_type] = []
            groups[resource.resource_type].append(resource)
        return groups
    
    def _optimize_resource_group(
        self,
        resource_type: ResourceType,
        resources: List[ResourceState],
        market_signals: List[MarketSignal],
        intervals: List[Tuple[datetime, datetime]],
        optimization_objective: OptimizationObjective
    ) -> Dict[str, List[OptimizationResult]]:
        """Optimize a group of resources of the same type"""
        
        if resource_type == ResourceType.BATTERY:
            return self._optimize_storage_resources(
                resources, market_signals, intervals, optimization_objective
            )
        elif resource_type in [ResourceType.SOLAR, ResourceType.WIND]:
            return self._optimize_renewable_resources(
                resources, market_signals, intervals, optimization_objective
            )
        elif resource_type == ResourceType.DEMAND_RESPONSE:
            return self._optimize_demand_response(
                resources, market_signals, intervals, optimization_objective
            )
        else:
            return self._optimize_generic_resources(
                resources, market_signals, intervals, optimization_objective
            )
    
    def _optimize_storage_resources(
        self,
        resources: List[ResourceState],
        market_signals: List[MarketSignal],
        intervals: List[Tuple[datetime, datetime]],
        optimization_objective: OptimizationObjective
    ) -> Dict[str, List[OptimizationResult]]:
        """Optimize storage resources using linear programming"""
        
        # Create optimization problem
        prob = LpProblem("Storage_Optimization", LpMaximize)
        
        # Create variables for each resource and interval
        power_vars = {}
        soc_vars = {}
        
        for resource in resources:
            for i, (start_time, end_time) in enumerate(intervals):
                # Power variable (positive for discharge, negative for charge)
                power_vars[(resource.resource_id, i)] = LpVariable(
                    f"power_{resource.resource_id}_{i}",
                    lowBound=-resource.constraints.max_power,
                    upBound=resource.constraints.max_power
                )
                
                # State of charge variable
                soc_vars[(resource.resource_id, i)] = LpVariable(
                    f"soc_{resource.resource_id}_{i}",
                    lowBound=resource.constraints.min_soc or 0,
                    upBound=resource.constraints.max_soc or 100
                )
        
        # Objective function components
        revenue_component = 0
        degradation_component = 0
        grid_support_component = 0
        
        for resource in resources:
            for i, (start_time, end_time) in enumerate(intervals):
                interval_signals = self._get_interval_signals(
                    market_signals, start_time, end_time
                )
                
                # Average price for interval
                avg_price = np.mean([signal.price for signal in interval_signals])
                
                # Revenue from energy arbitrage
                interval_hours = (end_time - start_time).total_seconds() / 3600
                revenue_component += power_vars[(resource.resource_id, i)] * avg_price * interval_hours
                
                # Battery degradation cost
                if resource.constraints.cycle_cost:
                    degradation_component += (
                        abs(power_vars[(resource.resource_id, i)]) * 
                        resource.constraints.cycle_cost * 
                        interval_hours
                    )
                
                # Grid support value
                for signal in interval_signals:
                    for service, price in signal.grid_service_prices.items():
                        if service in resource.grid_services_enabled:
                            grid_support_component += (
                                abs(power_vars[(resource.resource_id, i)]) * 
                                price * 
                                interval_hours
                            )
        
        # Combined objective with weights
        prob += (
            optimization_objective.revenue_weight * revenue_component -
            optimization_objective.battery_degradation_weight * degradation_component +
            optimization_objective.grid_support_weight * grid_support_component
        )
        
        # Add constraints
        for resource in resources:
            # Initial SOC constraint
            prob += soc_vars[(resource.resource_id, 0)] == resource.state_of_charge
            
            for i in range(len(intervals) - 1):
                # SOC continuity constraint
                prob += (
                    soc_vars[(resource.resource_id, i + 1)] == 
                    soc_vars[(resource.resource_id, i)] - 
                    power_vars[(resource.resource_id, i)] * 
                    resource.constraints.efficiency
                )
                
                # Ramp rate constraints
                prob += (
                    power_vars[(resource.resource_id, i + 1)] - 
                    power_vars[(resource.resource_id, i)] <= 
                    resource.constraints.ramp_up_rate
                )
                prob += (
                    power_vars[(resource.resource_id, i)] - 
                    power_vars[(resource.resource_id, i + 1)] <= 
                    resource.constraints.ramp_down_rate
                )
        
        # Solve optimization problem
        prob.solve()
        
        # Extract results
        results = {}
        for resource in resources:
            resource_results = []
            
            for i, (start_time, end_time) in enumerate(intervals):
                power = value(power_vars[(resource.resource_id, i)])
                soc = value(soc_vars[(resource.resource_id, i)])
                
                # Calculate economics
                interval_signals = self._get_interval_signals(
                    market_signals, start_time, end_time
                )
                avg_price = np.mean([signal.price for signal in interval_signals])
                interval_hours = (end_time - start_time).total_seconds() / 3600
                
                result = OptimizationResult(
                    resource_id=resource.resource_id,
                    target_power=power,
                    start_time=start_time,
                    end_time=end_time,
                    expected_cost=abs(power) * resource.constraints.cycle_cost * interval_hours if power < 0 else 0,
                    expected_revenue=power * avg_price * interval_hours if power > 0 else 0,
                    expected_soc=soc,
                    grid_service_contribution=self._calculate_grid_services(
                        resource, power, interval_signals
                    )
                )
                
                resource_results.append(result)
            
            results[resource.resource_id] = resource_results
        
        return results
    
    def _optimize_renewable_resources(
        self,
        resources: List[ResourceState],
        market_signals: List[MarketSignal],
        intervals: List[Tuple[datetime, datetime]],
        optimization_objective: OptimizationObjective
    ) -> Dict[str, List[OptimizationResult]]:
        """Optimize renewable resources considering weather forecasts"""
        results = {}
        
        for resource in resources:
            resource_results = []
            
            for start_time, end_time in intervals:
                # Get weather forecast for interval
                if resource.weather_forecast:
                    forecast_power = self._calculate_forecast_power(
                        resource, start_time, end_time
                    )
                else:
                    forecast_power = resource.current_power
                
                interval_signals = self._get_interval_signals(
                    market_signals, start_time, end_time
                )
                
                # Calculate optimal curtailment based on prices and grid services
                optimal_power = self._optimize_renewable_output(
                    resource, forecast_power, interval_signals, optimization_objective
                )
                
                # Calculate economics
                avg_price = np.mean([signal.price for signal in interval_signals])
                interval_hours = (end_time - start_time).total_seconds() / 3600
                
                result = OptimizationResult(
                    resource_id=resource.resource_id,
                    target_power=optimal_power,
                    start_time=start_time,
                    end_time=end_time,
                    expected_cost=0,  # Assume zero marginal cost
                    expected_revenue=optimal_power * avg_price * interval_hours,
                    grid_service_contribution=self._calculate_grid_services(
                        resource, optimal_power, interval_signals
                    ),
                    carbon_impact=-optimal_power * interval_hours  # Negative because it's carbon saving
                )
                
                resource_results.append(result)
            
            results[resource.resource_id] = resource_results
        
        return results
    
    def _optimize_demand_response(
        self,
        resources: List[ResourceState],
        market_signals: List[MarketSignal],
        intervals: List[Tuple[datetime, datetime]],
        optimization_objective: OptimizationObjective
    ) -> Dict[str, List[OptimizationResult]]:
        """Optimize demand response resources"""
        # Similar structure to other optimization methods
        # Implementation specific to demand response
        pass
    
    def _optimize_generic_resources(
        self,
        resources: List[ResourceState],
        market_signals: List[MarketSignal],
        intervals: List[Tuple[datetime, datetime]],
        optimization_objective: OptimizationObjective
    ) -> Dict[str, List[OptimizationResult]]:
        """Optimize other resource types"""
        # Generic optimization method for other resource types
        pass
    
    def _calculate_forecast_power(
        self,
        resource: ResourceState,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Calculate forecast power output based on weather forecast"""
        if not resource.weather_forecast:
            return resource.current_power
            
        # Implementation depends on resource type and weather model
        if resource.resource_type == ResourceType.SOLAR:
            return self._calculate_solar_power(resource, start_time, end_time)
        elif resource.resource_type == ResourceType.WIND:
            return self._calculate_wind_power(resource, start_time, end_time)
        else:
            return resource.current_power
    
    def _calculate_grid_services(
        self,
        resource: ResourceState,
        power: float,
        market_signals: List[MarketSignal]
    ) -> Dict[GridService, float]:
        """Calculate grid services provided by resource"""
        services = {}
        
        for service in resource.grid_services_enabled:
            if service == GridService.FREQUENCY_REGULATION:
                # Calculate regulation capacity
                services[service] = min(
                    abs(power),
                    resource.constraints.max_power * 0.1  # Assume 10% for regulation
                )
            elif service == GridService.VOLTAGE_SUPPORT:
                # Calculate reactive power capability
                services[service] = abs(power) * 0.3  # Assume 0.3 power factor
            # Add other grid services calculations
            
        return services
    
    def _calculate_risk_metrics(self, schedule: DispatchSchedule) -> Dict[str, float]:
        """Calculate risk metrics for the schedule"""
        return {
            "price_risk": self._calculate_price_risk(schedule),
            "weather_risk": self._calculate_weather_risk(schedule),
            "technical_risk": self._calculate_technical_risk(schedule)
        }
    
    def _calculate_carbon_savings(self, schedule: DispatchSchedule) -> float:
        """Calculate total carbon savings from the schedule"""
        total_savings = 0.0
        
        for resource_schedule in schedule.resources.values():
            for result in resource_schedule:
                if result.carbon_impact:
                    total_savings -= result.carbon_impact  # Negative because impact is negative
                    
        return total_savings
    
    def _calculate_intervals(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Tuple[datetime, datetime]]:
        """Calculate optimization intervals"""
        intervals = []
        current_time = start_time
        
        while current_time < end_time:
            interval_end = min(
                current_time + timedelta(minutes=self.interval_minutes),
                end_time
            )
            intervals.append((current_time, interval_end))
            current_time = interval_end
            
        return intervals
    
    def _get_interval_signals(
        self,
        market_signals: List[MarketSignal],
        start_time: datetime,
        end_time: datetime
    ) -> List[MarketSignal]:
        """Get market signals for specific interval"""
        return [
            signal for signal in market_signals
            if start_time <= signal.timestamp < end_time
        ]
    
    def _optimize_interval(
        self,
        resource: ResourceState,
        market_signals: List[MarketSignal],
        start_time: datetime,
        end_time: datetime
    ) -> OptimizationResult:
        """Optimize single interval for a resource"""
        
        # Calculate average market conditions
        avg_price = np.mean([signal.price for signal in market_signals])
        avg_demand = np.mean([signal.demand for signal in market_signals])
        
        # Consider resource constraints
        constraints = resource.constraints
        max_power_change = constraints.ramp_up_rate * (end_time - start_time).total_seconds() / 60
        
        # Calculate optimal power based on simple price threshold strategy
        # (This should be replaced with more sophisticated optimization algorithm)
        if avg_price > self.config.get('high_price_threshold', 100):
            # High price - maximize output within constraints
            target_power = min(
                constraints.max_power,
                resource.current_power + max_power_change
            )
        else:
            # Low price - minimize output within constraints
            target_power = max(
                constraints.min_power,
                resource.current_power - max_power_change
            )
            
        # Calculate economics
        duration_hours = (end_time - start_time).total_seconds() / 3600
        energy_mwh = target_power * duration_hours
        cost = energy_mwh * constraints.efficiency * avg_price
        revenue = energy_mwh * avg_price
        
        # Check for constraint violations
        violations = []
        if target_power > constraints.max_power:
            violations.append("max_power_exceeded")
        if target_power < constraints.min_power:
            violations.append("min_power_exceeded")
        
        return OptimizationResult(
            resource_id=resource.resource_id,
            target_power=target_power,
            start_time=start_time,
            end_time=end_time,
            expected_cost=cost,
            expected_revenue=revenue,
            constraints_violated=violations
        )

    def optimize_dispatch(self, current_state: Dict[str, Any], target_dispatch: Dict[str, float]) -> Dict[str, Any]:
        # ... existing optimization logic ...
        
        # If simulator is available, validate solution with simulation
        if self.simulator:
            simulation_results = self.simulator.step(proposed_dispatch)
            # Adjust dispatch based on simulation results
            for component_id, result in simulation_results.items():
                if abs(result['power_output'] - proposed_dispatch[component_id]['power_request']) > 0.01:
                    # Adjust dispatch if simulation shows significant deviation
                    proposed_dispatch[component_id]['power_request'] = result['power_output']
        
        return proposed_dispatch 