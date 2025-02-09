from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio
import httpx
from ..models.test_case import (
    TestCase,
    TestStep,
    TestResult,
    TestStatus,
    TestExecution
)
import structlog
from opentelemetry import trace
from prometheus_client import Counter, Histogram

logger = structlog.get_logger()
tracer = trace.get_tracer(__name__)
REQUEST_COUNT = Counter('test_requests_total', 'Total test executions')
TEST_DURATION = Histogram('test_duration_seconds', 'Test execution duration')

class TestExecutor:
    """Service for executing test cases"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.logger = logger.bind(service="test_executor")
        
    def _validate_environment(self, environment: Dict[str, str]) -> bool:
        """Validate the test environment configuration"""
        if not environment:
            return False
            
        # Check if all required service URLs are present
        for key in environment:
            if key.endswith('_URL') and not environment[key]:
                return False
                
        return True

    async def execute_test_case(self, test_case: TestCase) -> TestExecution:
        """Execute a test case with monitoring and security checks"""
        REQUEST_COUNT.inc()
        
        with (
            TEST_DURATION.time(),
            tracer.start_as_current_span("execute_test_case") as span,
            self.logger.contextualize(test_id=test_case.test_id)
        ):
            span.set_attribute("test_id", test_case.test_id)
            
            try:
                # Validate input
                self._validate_test_case(test_case)
                
                # Execute test steps
                execution = await self._execute_steps(test_case)
                
                # Record metrics and traces
                self._record_execution_metrics(execution)
                
                return execution
                
            except Exception as e:
                self.logger.error("Test execution failed", error=str(e))
                return TestExecution(
                    test_case=test_case,
                    status=TestStatus.ERROR,
                    error_message=str(e)
                )
    
    async def _execute_step(
        self,
        step: TestStep,
        environment: Dict[str, str]
    ) -> TestResult:
        """Execute a single test step"""
        result = TestResult(
            step_id=step.step_id,
            status=TestStatus.RUNNING,
            start_time=datetime.utcnow()
        )
        
        try:
            # Build service URL
            service_url = environment.get(f"{step.service}_URL")
            if not service_url:
                result.status = TestStatus.ERROR
                result.error_message = f"URL not found for service: {step.service}"
                return result
                
            # Execute operation with retries
            for attempt in range(step.retry_count):
                try:
                    response = await self._call_service(
                        service_url,
                        step.operation,
                        step.input_data
                    )
                    
                    result.actual_output = response
                    
                    # Validate response
                    if await self._validate_response(
                        response,
                        step.expected_output,
                        step.validation_rules
                    ):
                        result.status = TestStatus.PASSED
                        break
                    else:
                        result.status = TestStatus.FAILED
                        result.error_message = "Response validation failed"
                        
                except Exception as e:
                    if attempt == step.retry_count - 1:
                        result.status = TestStatus.ERROR
                        result.error_message = str(e)
                    await asyncio.sleep(1)  # Wait before retry
                    
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_message = str(e)
            
        finally:
            result.end_time = datetime.utcnow()
            
        return result
    
    async def _call_service(
        self,
        base_url: str,
        operation: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make HTTP call to service endpoint"""
        url = f"{base_url.rstrip('/')}/{operation.lstrip('/')}"
        
        async with self.http_client as client:
            response = await client.post(url, json=input_data)
            response.raise_for_status()
            return response.json()
    
    async def _validate_response(
        self,
        actual: Dict[str, Any],
        expected: Optional[Dict[str, Any]],
        rules: Dict[str, Any]
    ) -> bool:
        """Validate response against expected output and rules"""
        # Check exact match if expected output provided
        if expected and actual != expected:
            return False
            
        # Apply validation rules
        for field, rule in rules.items():
            value = actual.get(field)
            
            # Required field check
            if rule.get("required", False) and value is None:
                return False
                
            # Type check
            if "type" in rule and not isinstance(value, eval(rule["type"])):
                return False
                
            # Range check
            if "min" in rule and value < rule["min"]:
                return False
            if "max" in rule and value > rule["max"]:
                return False
                
            # Custom validation function
            if "validate" in rule:
                if not eval(rule["validate"])(value):
                    return False
                    
        return True
    
    def close(self):
        """Cleanup resources"""
        if self.http_client:
            asyncio.create_task(self.http_client.aclose()) 