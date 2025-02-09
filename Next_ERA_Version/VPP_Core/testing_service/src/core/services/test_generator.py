from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid
from ..models.test_case import (
    TestCase,
    TestStep,
    TestType,
    TestSuite
)

class TestGenerator:
    """Service for generating test cases"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    def generate_service_test_suite(
        self,
        service_name: str,
        endpoints: List[Dict[str, Any]]
    ) -> TestSuite:
        """Generate a test suite for a service"""
        test_cases = []
        
        # Generate basic health check test
        test_cases.append(self._generate_health_check(service_name))
        
        # Generate endpoint tests
        for endpoint in endpoints:
            test_cases.extend(self._generate_endpoint_tests(service_name, endpoint))
            
        return TestSuite(
            suite_id=f"suite_{uuid.uuid4()}",
            name=f"{service_name}_test_suite",
            description=f"Automated test suite for {service_name}",
            test_cases=test_cases,
            environment={
                f"{service_name}_URL": f"http://{service_name}:8000"
            },
            tags=[service_name, "automated"]
        )
        
    def _generate_health_check(self, service_name: str) -> TestCase:
        """Generate health check test case"""
        return TestCase(
            test_id=f"test_{uuid.uuid4()}",
            name=f"{service_name}_health_check",
            description=f"Health check test for {service_name}",
            type=TestType.INTEGRATION,
            services=[service_name],
            steps=[
                TestStep(
                    step_id=f"step_{uuid.uuid4()}",
                    service=service_name,
                    operation="health",
                    input_data={},
                    validation_rules={
                        "status": {
                            "required": True,
                            "type": "str",
                            "validate": "lambda x: x == 'healthy'"
                        }
                    }
                )
            ],
            environment={
                f"{service_name}_URL": f"http://{service_name}:8000"
            },
            tags=["health_check"]
        )
        
    def _generate_endpoint_tests(
        self,
        service_name: str,
        endpoint: Dict[str, Any]
    ) -> List[TestCase]:
        """Generate test cases for an endpoint"""
        test_cases = []
        
        # Basic functionality test
        test_cases.append(
            TestCase(
                test_id=f"test_{uuid.uuid4()}",
                name=f"{service_name}_{endpoint['path']}_basic",
                description=f"Basic functionality test for {endpoint['path']}",
                type=TestType.INTEGRATION,
                services=[service_name],
                steps=[
                    TestStep(
                        step_id=f"step_{uuid.uuid4()}",
                        service=service_name,
                        operation=endpoint['path'],
                        input_data=self._generate_test_data(endpoint['input_schema']),
                        validation_rules=self._generate_validation_rules(
                            endpoint['output_schema']
                        )
                    )
                ],
                environment={
                    f"{service_name}_URL": f"http://{service_name}:8000"
                },
                tags=[service_name, endpoint['path'], "basic"]
            )
        )
        
        # Error handling test
        test_cases.append(
            TestCase(
                test_id=f"test_{uuid.uuid4()}",
                name=f"{service_name}_{endpoint['path']}_error",
                description=f"Error handling test for {endpoint['path']}",
                type=TestType.INTEGRATION,
                services=[service_name],
                steps=[
                    TestStep(
                        step_id=f"step_{uuid.uuid4()}",
                        service=service_name,
                        operation=endpoint['path'],
                        input_data=self._generate_invalid_data(
                            endpoint['input_schema']
                        ),
                        validation_rules={
                            "error": {
                                "required": True,
                                "type": "dict"
                            }
                        }
                    )
                ],
                environment={
                    f"{service_name}_URL": f"http://{service_name}:8000"
                },
                tags=[service_name, endpoint['path'], "error"]
            )
        )
        
        # Performance test
        test_cases.append(
            TestCase(
                test_id=f"test_{uuid.uuid4()}",
                name=f"{service_name}_{endpoint['path']}_performance",
                description=f"Performance test for {endpoint['path']}",
                type=TestType.PERFORMANCE,
                services=[service_name],
                steps=[TestStep(
                    step_id=f"step_{uuid.uuid4()}",
                    service=service_name,
                    operation=endpoint['path'],
                    input_data=self._generate_test_data(endpoint['input_schema']),
                    validation_rules={
                        "response_time": {
                            "type": "float",
                            "max": 1.0  # 1 second max response time
                        }
                    }
                )],
                environment={
                    f"{service_name}_URL": f"http://{service_name}:8000"
                },
                tags=[service_name, endpoint['path'], "performance"]
            )
        )
        
        return test_cases
        
    def _generate_test_data(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test data based on schema"""
        # TODO: Implement more sophisticated test data generation
        data = {}
        for field, field_schema in schema.items():
            if field_schema.get("type") == "string":
                data[field] = f"test_{uuid.uuid4()}"
            elif field_schema.get("type") == "number":
                data[field] = 42.0
            elif field_schema.get("type") == "integer":
                data[field] = 42
            elif field_schema.get("type") == "boolean":
                data[field] = True
            elif field_schema.get("type") == "array":
                data[field] = []
            elif field_schema.get("type") == "object":
                data[field] = {}
        return data
        
    def _generate_invalid_data(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate invalid test data based on schema"""
        # TODO: Implement more sophisticated invalid data generation
        data = {}
        for field, field_schema in schema.items():
            if field_schema.get("type") == "string":
                data[field] = 42  # Wrong type
            elif field_schema.get("type") == "number":
                data[field] = "not_a_number"  # Wrong type
            elif field_schema.get("type") == "integer":
                data[field] = "not_an_integer"  # Wrong type
            elif field_schema.get("type") == "boolean":
                data[field] = "not_a_boolean"  # Wrong type
            elif field_schema.get("type") == "array":
                data[field] = "not_an_array"  # Wrong type
            elif field_schema.get("type") == "object":
                data[field] = "not_an_object"  # Wrong type
        return data
        
    def _generate_validation_rules(
        self,
        schema: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Generate validation rules based on schema"""
        rules = {}
        for field, field_schema in schema.items():
            rule = {
                "required": field_schema.get("required", False),
                "type": field_schema.get("type", "any")
            }
            
            if "minimum" in field_schema:
                rule["min"] = field_schema["minimum"]
            if "maximum" in field_schema:
                rule["max"] = field_schema["maximum"]
                
            rules[field] = rule
            
        return rules 