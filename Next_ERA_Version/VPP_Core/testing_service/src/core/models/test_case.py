from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field

class TestType(str, Enum):
    """Types of tests that can be performed"""
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    BEHAVIOR = "behavior"
    STRESS = "stress"
    SECURITY = "security"

class TestStatus(str, Enum):
    """Status of test execution"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"

class TestStep(BaseModel):
    """Individual test step"""
    step_id: str
    service: str
    operation: str
    input_data: Dict[str, Any]
    expected_output: Optional[Dict[str, Any]] = None
    validation_rules: Dict[str, Any]
    timeout_seconds: int = 30
    retry_count: int = 3
    dependencies: List[str] = Field(default_factory=list)

class TestResult(BaseModel):
    """Result of a test step execution"""
    step_id: str
    status: TestStatus
    actual_output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    performance_metrics: Optional[Dict[str, float]] = None

class TestCase(BaseModel):
    """Complete test case definition"""
    test_id: str
    name: str
    description: str
    type: TestType
    priority: int = 1
    services: List[str]
    steps: List[TestStep]
    environment: Dict[str, str]
    timeout_minutes: int = 30
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)

class TestSuite(BaseModel):
    """Collection of test cases"""
    suite_id: str
    name: str
    description: str
    test_cases: List[TestCase]
    parallel_execution: bool = False
    environment: Dict[str, str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)

class TestExecution(BaseModel):
    """Test execution details"""
    execution_id: str
    test_case: TestCase
    status: TestStatus
    results: List[TestResult] = Field(default_factory=list)
    start_time: datetime
    end_time: Optional[datetime] = None
    environment: Dict[str, str]
    triggered_by: str
    logs: List[str] = Field(default_factory=list)

    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate test execution metrics"""
        total_steps = len(self.test_case.steps)
        completed_steps = len(self.results)
        passed_steps = len([r for r in self.results if r.status == TestStatus.PASSED])
        
        return {
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "passed_steps": passed_steps,
            "pass_rate": (passed_steps / total_steps * 100) if total_steps > 0 else 0,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time else None
        } 