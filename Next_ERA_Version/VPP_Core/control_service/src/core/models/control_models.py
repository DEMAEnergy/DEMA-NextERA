from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class PIDController:
    """PID Controller implementation with adaptive tuning capabilities"""
    kp: float  # Proportional gain
    ki: float  # Integral gain
    kd: float  # Derivative gain
    
    def __post_init__(self):
        self.previous_error: float = 0.0
        self.integral: float = 0.0
        self.last_update: Optional[datetime] = None
        
    def calculate(self, error: float) -> float:
        """Calculate control output using PID algorithm"""
        now = datetime.utcnow()
        
        # Initialize time tracking
        if self.last_update is None:
            self.last_update = now
            dt = 0.1  # Default time step on first update
        else:
            dt = (now - self.last_update).total_seconds()
            dt = max(0.001, min(dt, 1.0))  # Limit dt between 1ms and 1s
        
        # Update integral term
        self.integral += error * dt
        
        # Calculate derivative term
        derivative = (error - self.previous_error) / dt if dt > 0 else 0
        
        # Calculate PID output
        output = (
            self.kp * error +  # Proportional term
            self.ki * self.integral +  # Integral term
            self.kd * derivative  # Derivative term
        )
        
        # Update state
        self.previous_error = error
        self.last_update = now
        
        return output
    
    def increase_response(self, factor: float = 1.1):
        """Increase controller response by scaling gains"""
        self.kp *= factor
        self.ki *= factor
        self.kd *= factor
        
    def decrease_response(self, factor: float = 0.9):
        """Decrease controller response by scaling gains"""
        self.kp *= factor
        self.ki *= factor
        self.kd *= factor
        
    def reset(self):
        """Reset controller state"""
        self.previous_error = 0.0
        self.integral = 0.0
        self.last_update = None

@dataclass
class ControlLoop:
    """Represents a complete control loop for a device"""
    device_id: str
    controller: PIDController
    
    def __post_init__(self):
        self.last_adjustment: float = 0.0
        self.adjustment_history: List[float] = []
        
    def calculate_adjustment(self, error: float) -> float:
        """Calculate control adjustment based on error"""
        adjustment = self.controller.calculate(error)
        
        # Apply reasonable limits to adjustment
        max_adjustment = 1.0  # Maximum allowed adjustment
        adjustment = max(-max_adjustment, min(adjustment, max_adjustment))
        
        # Store adjustment history
        self.last_adjustment = adjustment
        self.adjustment_history.append(adjustment)
        
        # Keep history manageable
        max_history = 1000
        if len(self.adjustment_history) > max_history:
            self.adjustment_history = self.adjustment_history[-max_history:]
        
        return adjustment
    
    def reset(self):
        """Reset control loop state"""
        self.controller.reset()
        self.last_adjustment = 0.0
        self.adjustment_history.clear() 