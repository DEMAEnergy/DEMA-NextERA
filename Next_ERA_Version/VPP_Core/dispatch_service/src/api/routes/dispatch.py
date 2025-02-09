from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timedelta
from ..schemas.dispatch import (
    CreateScheduleRequest,
    ScheduleResponse,
    UpdateScheduleRequest,
    ScheduleStatus
)
from ...core.services.optimizer import DispatchOptimizer
from ...infrastructure.messaging.kafka_producer import KafkaProducer
from ..core.simulation.simulator import SimulationConfig, VPPSimulator

router = APIRouter(prefix="/dispatch", tags=["dispatch"])
simulator = None

@router.post("/initialize_simulation")
async def initialize_simulation(config: SimulationConfig):
    global simulator
    simulator = VPPSimulator(config)
    return {"status": "simulation initialized"}

@router.post("/dispatch")
async def create_dispatch(dispatch_request: DispatchRequest):
    # ... existing code ...
    
    optimizer = Optimizer(config=optimizer_config, simulator=simulator if simulator else None)
    dispatch_result = optimizer.optimize_dispatch(current_state, target_dispatch)
    
    # If in simulation mode, include simulation results
    if simulator:
        simulation_results = simulator.step(dispatch_result)
        return {
            "dispatch": dispatch_result,
            "simulation_results": simulation_results
        }
    
    return {"dispatch": dispatch_result}

@router.post("/schedule", response_model=ScheduleResponse)
async def create_schedule(
    request: CreateScheduleRequest,
    optimizer: DispatchOptimizer = Depends(),
    kafka: KafkaProducer = Depends()
):
    """Create a new dispatch schedule"""
    try:
        # Create schedule
        schedule = await optimizer.create_dispatch_schedule(
            resources=request.resources,
            market_signals=request.market_signals,
            start_time=request.start_time,
            end_time=request.end_time
        )
        
        # Validate schedule
        if not schedule.validate_schedule():
            raise HTTPException(
                status_code=400,
                detail="Generated schedule violates constraints"
            )
            
        # Publish schedule to Kafka
        await kafka.publish_schedule(schedule)
        
        return ScheduleResponse(
            schedule_id=schedule.schedule_id,
            status="created",
            schedule=schedule,
            metrics=schedule.calculate_metrics()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create schedule: {str(e)}"
        )

@router.get("/schedule/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: str):
    """Get existing schedule by ID"""
    # TODO: Implement schedule retrieval from database
    raise HTTPException(status_code=501, detail="Not implemented")

@router.put("/schedule/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: str,
    request: UpdateScheduleRequest,
    optimizer: DispatchOptimizer = Depends(),
    kafka: KafkaProducer = Depends()
):
    """Update existing schedule"""
    # TODO: Implement schedule update
    raise HTTPException(status_code=501, detail="Not implemented")

@router.delete("/schedule/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    kafka: KafkaProducer = Depends()
):
    """Delete existing schedule"""
    # TODO: Implement schedule deletion
    raise HTTPException(status_code=501, detail="Not implemented")

@router.post("/schedule/{schedule_id}/execute")
async def execute_schedule(
    schedule_id: str,
    kafka: KafkaProducer = Depends()
):
    """Start schedule execution"""
    try:
        # Publish execution command to Kafka
        await kafka.publish_command(
            topic="schedule_execution",
            key=schedule_id,
            value={
                "command": "execute",
                "schedule_id": schedule_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return {"status": "execution_started", "schedule_id": schedule_id}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start schedule execution: {str(e)}"
        )

@router.post("/schedule/{schedule_id}/stop")
async def stop_schedule(
    schedule_id: str,
    kafka: KafkaProducer = Depends()
):
    """Stop schedule execution"""
    try:
        # Publish stop command to Kafka
        await kafka.publish_command(
            topic="schedule_execution",
            key=schedule_id,
            value={
                "command": "stop",
                "schedule_id": schedule_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return {"status": "execution_stopped", "schedule_id": schedule_id}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop schedule execution: {str(e)}"
        )

@router.get("/schedule/{schedule_id}/status", response_model=ScheduleStatus)
async def get_schedule_status(schedule_id: str):
    """Get current status of schedule execution"""
    # TODO: Implement status retrieval
    raise HTTPException(status_code=501, detail="Not implemented") 