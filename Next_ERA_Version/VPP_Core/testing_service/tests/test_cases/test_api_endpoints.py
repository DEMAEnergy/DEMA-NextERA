import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from typing import Dict, Any
from src.main import app
from src.core.models.test_case import (
    TestCase,
    TestSuite,
    TestType,
    TestStatus
)

@pytest.fixture
def test_client():
    """Test client fixture"""
    client = TestClient(app)
    return client

@pytest.fixture
def sample_test_case_data() -> Dict[str, Any]:
    """Sample test case data fixture"""
    return {
        "test_case": {
            "test_id": "test_123",
            "name": "sample_test",
            "description": "Sample test case",
            "type": TestType.INTEGRATION,
            "services": ["dispatch"],
            "steps": [{
                "step_id": "step_1",
                "service": "dispatch",
                "operation": "schedule",
                "input_data": {
                    "resources": [{"id": "battery_1", "capacity": 100}],
                    "start_time": datetime.utcnow().isoformat(),
                    "end_time": datetime.utcnow().isoformat()
                },
                "validation_rules": {
                    "schedule_id": {"required": True, "type": "str"}
                }
            }],
            "environment": {"dispatch_URL": "http://dispatch:8001"}
        },
        "labels": {"priority": "high", "category": "dispatch"}
    }

@pytest.fixture
def sample_test_suite_data(sample_test_case_data) -> Dict[str, Any]:
    """Sample test suite data fixture"""
    return {
        "test_suite": {
            "suite_id": "suite_123",
            "name": "sample_suite",
            "description": "Sample test suite",
            "test_cases": [sample_test_case_data["test_case"]],
            "environment": {"dispatch_URL": "http://dispatch:8001"}
        },
        "labels": {"priority": "high", "category": "integration"}
    }

def test_create_test_case(test_client):
    """Test creating a test case"""
    response = test_client.post("/tests/case", json={
        "test_case": {
            "test_id": "test_123",
            "name": "sample_test",
            "description": "Sample test case",
            "type": TestType.INTEGRATION,
            "services": ["dispatch"],
            "steps": [{
                "step_id": "step_1",
                "service": "dispatch",
                "operation": "schedule",
                "input_data": {
                    "resources": [{"id": "battery_1", "capacity": 100}],
                    "start_time": datetime.utcnow().isoformat(),
                    "end_time": datetime.utcnow().isoformat()
                },
                "validation_rules": {
                    "schedule_id": {"required": True, "type": "str"}
                }
            }],
            "environment": {"dispatch_URL": "http://dispatch:8001"}
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert "test_id" in data
    assert data["status"] == "created"

def test_create_test_suite(test_client, sample_test_suite_data):
    """Test creating a test suite"""
    response = test_client.post("/tests/suite", json=sample_test_suite_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "suite_id" in data
    assert data["status"] == "created"
    assert data["test_suite"]["name"] == sample_test_suite_data["test_suite"]["name"]

def test_execute_test_case(test_client):
    """Test executing a test case"""
    test_id = "test_123"
    response = test_client.post(f"/tests/case/{test_id}/execute")
    
    assert response.status_code == 200
    data = response.json()
    assert "execution_id" in data
    assert data["status"] == TestStatus.PENDING
    assert "message" in data

def test_execute_test_suite(test_client):
    """Test executing a test suite"""
    suite_id = "suite_123"
    response = test_client.post(f"/tests/suite/{suite_id}/execute")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for execution in data:
        assert "execution_id" in execution
        assert execution["status"] == TestStatus.PENDING
        assert "message" in execution

def test_get_execution_status(test_client):
    """Test getting execution status"""
    execution_id = "exec_123"
    response = test_client.get(f"/tests/executions/{execution_id}")
    
    # Since this endpoint is not implemented yet, we expect 501
    assert response.status_code == 501

def test_list_test_cases(test_client):
    """Test listing test cases"""
    # Test with no filters
    response = test_client.get("/tests/cases")
    assert response.status_code == 501  # Not implemented yet
    
    # Test with filters
    response = test_client.get("/tests/cases", params={
        "type": TestType.INTEGRATION,
        "service": "dispatch",
        "status": TestStatus.PASSED,
        "tags": ["performance"]
    })
    assert response.status_code == 501  # Not implemented yet

def test_list_test_suites(test_client):
    """Test listing test suites"""
    # Test with no filters
    response = test_client.get("/tests/suites")
    assert response.status_code == 501  # Not implemented yet
    
    # Test with tags filter
    response = test_client.get("/tests/suites", params={
        "tags": ["integration", "dispatch"]
    })
    assert response.status_code == 501  # Not implemented yet

def test_invalid_test_case(test_client):
    """Test creating invalid test case"""
    # Missing required fields
    invalid_data = {
        "test_case": {
            "name": "invalid_test"
            # Missing other required fields
        }
    }
    response = test_client.post("/tests/case", json=invalid_data)
    assert response.status_code == 422  # Validation error

def test_invalid_test_suite(test_client):
    """Test creating invalid test suite"""
    # Missing required fields
    invalid_data = {
        "test_suite": {
            "name": "invalid_suite"
            # Missing other required fields
        }
    }
    response = test_client.post("/tests/suite", json=invalid_data)
    assert response.status_code == 422  # Validation error

def test_nonexistent_test_case(test_client):
    """Test executing nonexistent test case"""
    test_id = "nonexistent"
    response = test_client.post(f"/tests/case/{test_id}/execute")
    assert response.status_code == 404

def test_nonexistent_test_suite(test_client):
    """Test executing nonexistent test suite"""
    suite_id = "nonexistent"
    response = test_client.post(f"/tests/suite/{suite_id}/execute")
    assert response.status_code == 404 