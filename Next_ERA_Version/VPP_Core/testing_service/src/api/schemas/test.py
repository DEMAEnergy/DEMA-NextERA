from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.core.models.test_case import (
    TestCase,
    TestSuite,
    TestExecution,
    TestStatus,
    TestType
)

class TestFilter(BaseModel):
    """Filter criteria for test cases"""
    type: Optional[TestType] = None
    service: Optional[str] = None
    status: Optional[TestStatus] = None
    tags: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class CreateTestCaseRequest(BaseModel):
    """Request to create a new test case"""
    test_case: TestCase
    labels: Optional[Dict[str, str]] = None

class CreateTestSuiteRequest(BaseModel):
    """Request to create a new test suite"""
    test_suite: TestSuite
    labels: Optional[Dict[str, str]] = None

class TestCaseResponse(BaseModel):
    """Response containing test case information"""
    test_id: str
    status: str
    test_case: TestCase
    created_at: datetime = datetime.utcnow()
    labels: Optional[Dict[str, str]] = None

class TestSuiteResponse(BaseModel):
    """Response containing test suite information"""
    suite_id: str
    status: str
    test_suite: TestSuite
    created_at: datetime = datetime.utcnow()
    labels: Optional[Dict[str, str]] = None

class TestExecutionResponse(BaseModel):
    """Response containing test execution information"""
    execution_id: str
    status: TestStatus
    message: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, float]] = None

class TestResultSummary(BaseModel):
    """Summary of test execution results"""
    total_tests: int
    passed: int
    failed: int
    error: int
    skipped: int
    duration_seconds: float
    pass_rate: float
    start_time: datetime
    end_time: datetime
    environment: Dict[str, str]

class ServiceTestConfig(BaseModel):
    """Configuration for service testing"""
    service_name: str
    base_url: str
    health_endpoint: str = "/health"
    timeout_seconds: int = 30
    retry_count: int = 3
    headers: Optional[Dict[str, str]] = None
    environment_variables: Optional[Dict[str, str]] = None 