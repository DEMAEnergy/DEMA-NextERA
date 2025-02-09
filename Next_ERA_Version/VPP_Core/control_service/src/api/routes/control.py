from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..schemas.control import (
    ControlSetpoint,
    ControlFeedback,
    ControlAdjustment,
    BatchControlRequest,
    ControlResponse
)
from ...core.services.control_service import ControlService

router = APIRouter(prefix="/control", tags=["control"])
control_service = ControlService()

@router.post("/setpoint", response_model=ControlResponse)
async def set_control_point(setpoint: ControlSetpoint):
    """Set a new control setpoint for a device"""
    return await control_service.process_setpoint(setpoint)

@router.post("/batch", response_model=List[ControlResponse])
async def batch_control(request: BatchControlRequest):
    """Process multiple control setpoints"""
    responses = []
    for setpoint in request.controls:
        response = await control_service.process_setpoint(setpoint)
        responses.append(response)
    return responses

@router.post("/feedback", response_model=ControlResponse)
async def record_control_feedback(feedback: ControlFeedback):
    """Record feedback from control implementation"""
    try:
        await control_service.record_feedback(feedback)
        # Trigger controller optimization after receiving feedback
        await control_service.optimize_controller(feedback.device_id)
        return ControlResponse(
            success=True,
            message="Feedback recorded successfully",
            data={"device_id": feedback.device_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/adjustment/{device_id}", response_model=ControlAdjustment)
async def get_control_adjustment(device_id: str, current_value: float):
    """Get control adjustment for a device based on current value"""
    try:
        return await control_service.apply_control(device_id, current_value)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset/{device_id}", response_model=ControlResponse)
async def reset_control_loop(device_id: str):
    """Reset the control loop for a device"""
    try:
        if device_id in control_service.control_loops:
            control_service.control_loops[device_id].reset()
            return ControlResponse(
                success=True,
                message=f"Control loop reset for device {device_id}"
            )
        raise HTTPException(status_code=404, detail=f"No control loop found for device {device_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 