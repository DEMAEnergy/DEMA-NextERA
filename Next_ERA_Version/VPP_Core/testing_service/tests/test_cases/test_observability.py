import pytest
import structlog
from opentelemetry import trace
from prometheus_client import Counter, Histogram
from src.core.services.test_executor import TestExecutor
from src.core.models.test_case import TestCase, TestStatus

# Set up logging
logger = structlog.get_logger()

# Set up tracing
tracer = trace.get_tracer(__name__)

# Set up metrics
REQUEST_COUNT = Counter('test_requests_total', 'Total test executions')
TEST_DURATION = Histogram('test_duration_seconds', 'Test execution duration')

@pytest.fixture
def monitored_executor(test_config) -> TestExecutor:
    """Create a test executor with monitoring"""
    executor = TestExecutor(test_config)
    # Add monitoring wrapper
    return executor

@pytest.mark.asyncio
async def test_logging_integration(monitored_executor, sample_test_case):
    """Test structured logging during test execution"""
    with logger.contextualize(test_id=sample_test_case.test_id):
        execution = await monitored_executor.execute_test_case(sample_test_case)
        
    assert execution.logs
    assert all('test_id' in log for log in execution.logs)
    assert all('timestamp' in log for log in execution.logs)

@pytest.mark.asyncio
async def test_metrics_collection(monitored_executor, sample_test_case):
    """Test metrics collection during test execution"""
    initial_count = REQUEST_COUNT._value.get()
    
    with TEST_DURATION.time():
        execution = await monitored_executor.execute_test_case(sample_test_case)
    
    assert REQUEST_COUNT._value.get() == initial_count + 1
    assert execution.status in [TestStatus.PASSED, TestStatus.FAILED]

@pytest.mark.asyncio
async def test_distributed_tracing(monitored_executor, sample_test_case):
    """Test distributed tracing integration"""
    with tracer.start_as_current_span("test_execution") as span:
        span.set_attribute("test_id", sample_test_case.test_id)
        execution = await monitored_executor.execute_test_case(sample_test_case)
        
    assert execution.trace_id  # Assuming we add trace_id to execution results 