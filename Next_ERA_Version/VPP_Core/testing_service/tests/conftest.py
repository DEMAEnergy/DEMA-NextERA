import pytest
import os
import asyncio
from typing import Dict, Any
from src.core.services.test_executor import TestExecutor
from src.core.services.test_generator import TestGenerator

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_executor():
    """Create test executor instance"""
    config = {
        "timeout_seconds": 30,
        "retry_count": 3
    }
    return TestExecutor(config)

@pytest.fixture
def test_generator():
    """Create test generator instance"""
    config = {
        "timeout_seconds": 30,
        "retry_count": 3
    }
    return TestGenerator(config)

@pytest.fixture(scope="session")
def test_environment() -> Dict[str, str]:
    """Test environment configuration"""
    return {
        "dispatch_URL": os.getenv("DISPATCH_URL", "http://dispatch:8001"),
        "control_URL": os.getenv("CONTROL_URL", "http://control:8002"),
        "grid_URL": os.getenv("GRID_URL", "http://grid:8003"),
        "emergency_URL": os.getenv("EMERGENCY_URL", "http://emergency:8004")
    }

@pytest.fixture(scope="session")
def test_config(test_environment) -> Dict[str, Any]:
    """Test configuration"""
    return {
        "environment": test_environment,
        "timeout_seconds": 30,
        "retry_count": 3,
        "parallel_execution": True,
        "log_level": "INFO"
    }

@pytest.fixture(scope="session")
def mock_services(test_environment):
    """Start mock services for testing"""
    # TODO: Implement mock services using something like aioresponses
    yield

@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for tests"""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    yield

@pytest.fixture
def mock_kafka():
    """Mock Kafka producer/consumer"""
    # TODO: Implement Kafka mocking
    yield

@pytest.fixture
def mock_database():
    """Mock database connections"""
    # TODO: Implement database mocking
    yield 