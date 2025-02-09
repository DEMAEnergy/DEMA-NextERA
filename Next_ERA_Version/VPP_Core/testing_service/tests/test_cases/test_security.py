import pytest
from src.core.services.test_executor import TestExecutor
from src.core.models.test_case import TestCase, TestStatus
import jwt
import aiohttp

@pytest.fixture
def security_test_case() -> TestCase:
    """Create a test case for security testing"""
    return TestCase(
        test_id="security_test_1",
        name="api_security_test",
        description="Test API security measures",
        type="SECURITY",
        steps=[
            {
                "step_id": "auth_test",
                "operation": "authenticate",
                "input_data": {"username": "test_user", "password": "test_pass"},
                "validation_rules": {"token": {"required": True}}
            }
        ]
    )

@pytest.mark.asyncio
async def test_rate_limiting(test_executor, security_test_case):
    """Test API rate limiting"""
    # Make multiple rapid requests
    responses = await asyncio.gather(*[
        test_executor.execute_test_case(security_test_case)
        for _ in range(10)
    ])
    
    # Check if rate limiting kicked in
    assert any(
        execution.status == TestStatus.ERROR and 
        "rate limit exceeded" in execution.error_message.lower()
        for execution in responses
    )

@pytest.mark.asyncio
async def test_input_validation(test_executor, security_test_case):
    """Test input validation and sanitization"""
    # Test SQL injection attempt
    security_test_case.steps[0].input_data["username"] = "'; DROP TABLE users; --"
    execution = await test_executor.execute_test_case(security_test_case)
    assert execution.status == TestStatus.ERROR
    
    # Test XSS attempt
    security_test_case.steps[0].input_data["username"] = "<script>alert('xss')</script>"
    execution = await test_executor.execute_test_case(security_test_case)
    assert execution.status == TestStatus.ERROR

@pytest.mark.asyncio
async def test_authentication(test_executor, security_test_case):
    """Test authentication mechanisms"""
    # Test invalid credentials
    security_test_case.steps[0].input_data["password"] = "wrong_password"
    execution = await test_executor.execute_test_case(security_test_case)
    assert execution.status == TestStatus.FAILED
    
    # Test token validation
    security_test_case.steps[0].input_data["password"] = "test_pass"
    execution = await test_executor.execute_test_case(security_test_case)
    assert execution.status == TestStatus.PASSED
    assert "token" in execution.results[0].response 