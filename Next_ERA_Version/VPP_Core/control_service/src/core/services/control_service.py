from datetime import datetime
import numpy as np
from typing import Dict, List, Optional
from ..models.control_models import ControlLoop, PIDController
from ...api.schemas.control import ControlSetpoint, ControlFeedback, ControlAdjustment

class ControlService:
    def __init__(self):
        self.control_loops: Dict[str, ControlLoop] = {}
        self.active_setpoints: Dict[str, ControlSetpoint] = {}
        self.feedback_history: Dict[str, List[ControlFeedback]] = {}
        
    async def process_setpoint(self, setpoint: ControlSetpoint) -> ControlResponse:
        """Process a new setpoint received from dispatch"""
        try:
            device_id = setpoint.device_id
            if device_id not in self.control_loops:
                self.control_loops[device_id] = ControlLoop(
                    device_id=device_id,
                    controller=PIDController(kp=1.0, ki=0.1, kd=0.05)
                )
            
            self.active_setpoints[device_id] = setpoint
            return ControlResponse(
                success=True,
                message=f"Setpoint processed for device {device_id}",
                data={"setpoint": setpoint.dict()}
            )
        except Exception as e:
            return ControlResponse(
                success=False,
                message=f"Error processing setpoint: {str(e)}"
            )

    async def apply_control(self, device_id: str, current_value: float) -> ControlAdjustment:
        """Calculate and apply control adjustment based on current value and setpoint"""
        if device_id not in self.active_setpoints:
            raise ValueError(f"No active setpoint for device {device_id}")
        
        setpoint = self.active_setpoints[device_id]
        control_loop = self.control_loops[device_id]
        
        error = setpoint.setpoint_value - current_value
        adjustment = control_loop.calculate_adjustment(error)
        
        confidence = self._calculate_confidence(error, adjustment)
        
        return ControlAdjustment(
            device_id=device_id,
            adjustment_value=adjustment,
            error_metric=abs(error),
            confidence=confidence,
            timestamp=datetime.utcnow()
        )

    async def record_feedback(self, feedback: ControlFeedback) -> None:
        """Record feedback for analysis and adjustment"""
        device_id = feedback.device_id
        if device_id not in self.feedback_history:
            self.feedback_history[device_id] = []
        
        self.feedback_history[device_id].append(feedback)
        
        # Trim history to keep only recent entries
        max_history = 1000
        if len(self.feedback_history[device_id]) > max_history:
            self.feedback_history[device_id] = self.feedback_history[device_id][-max_history:]

    async def optimize_controller(self, device_id: str) -> None:
        """Optimize controller parameters based on feedback history"""
        if device_id not in self.feedback_history:
            return
        
        history = self.feedback_history[device_id]
        if len(history) < 10:  # Need minimum history for optimization
            return
            
        errors = [fb.error for fb in history[-10:]]
        mean_error = np.mean(np.abs(errors))
        
        # Simple adaptive tuning based on error magnitude
        control_loop = self.control_loops[device_id]
        if mean_error > 0.1:  # Error threshold for adaptation
            control_loop.controller.increase_response()
        elif mean_error < 0.01:  # Good performance threshold
            control_loop.controller.decrease_response()

    def _calculate_confidence(self, error: float, adjustment: float) -> float:
        """Calculate confidence level in control adjustment"""
        # Simple confidence calculation based on error magnitude
        max_acceptable_error = 0.1
        confidence = 1.0 - min(abs(error) / max_acceptable_error, 1.0)
        
        # Reduce confidence for large adjustments
        max_adjustment = 1.0
        adjustment_factor = 1.0 - min(abs(adjustment) / max_adjustment, 1.0)
        
        return min(confidence * adjustment_factor, 1.0) 