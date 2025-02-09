# VPP Service Template

## Standard Service Structure
```
service_name/
├── src/
│   ├── api/                 # API endpoints and interfaces
│   │   ├── routes/         # Route definitions
│   │   ├── schemas/        # Request/response schemas
│   │   └── validators/     # Input validation
│   ├── core/               # Core business logic
│   │   ├── models/         # Domain models
│   │   ├── services/       # Business services
│   │   └── utils/          # Utility functions
│   ├── infrastructure/     # External dependencies
│   │   ├── database/       # Database connections
│   │   ├── messaging/      # Message queue handlers
│   │   └── external/       # External service clients
│   └── config/             # Configuration management
├── tests/                  # Test suites
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── fixtures/          # Test data
├── Dockerfile             # Container definition
├── requirements.txt       # Python dependencies
├── setup.py              # Package setup
└── README.md             # Service documentation
```

## Standard Dependencies
```python
# Core Dependencies
fastapi>=0.68.0          # Web framework
pydantic>=1.8.2          # Data validation
uvicorn>=0.15.0          # ASGI server
python-dotenv>=0.19.0    # Environment management

# Messaging
kafka-python>=2.0.2      # Kafka client
aio-pika>=7.1.0          # AMQP client

# Database
sqlalchemy>=1.4.23       # SQL ORM
databases>=0.5.2         # Async database

# Monitoring
prometheus-client>=0.11.0 # Metrics
opentelemetry-api>=1.4.1  # Tracing
```

## Standard Interfaces

### 1. Health Check
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": service_version
    }
```

### 2. Metrics
```python
@app.get("/metrics")
async def metrics():
    return {
        "service_metrics": collect_metrics(),
        "timestamp": datetime.utcnow()
    }
```

### 3. Service Status
```python
@app.get("/status")
async def status():
    return {
        "service": service_name,
        "status": service_status,
        "dependencies": check_dependencies(),
        "timestamp": datetime.utcnow()
    }
```

## Standard Configuration

```python
class ServiceConfig(BaseSettings):
    # Service Identity
    SERVICE_NAME: str
    SERVICE_VERSION: str
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_CONSUMER_GROUP: str
    
    # Database Configuration
    DATABASE_URL: str
    
    # Security
    API_KEY: str
    JWT_SECRET: str
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    TRACING_ENABLED: bool = True
    
    class Config:
        env_file = ".env"
```

## Standard Logging

```python
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "json": {
            "format": "json",
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout"
        }
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "INFO"
        }
    }
}
```

## Error Handling

```python
class ServiceError(Exception):
    def __init__(self, code: str, message: str, details: Optional[dict] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
```

## Testing Standards

```python
# Standard test fixture
@pytest.fixture
def service_client():
    app = create_app()
    return TestClient(app)

# Standard test format
def test_service_endpoint(service_client):
    response = service_client.get("/endpoint")
    assert response.status_code == 200
    assert "expected_key" in response.json()
```

## Deployment Standards

### 1. Health Checks
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### 2. Resource Limits
```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### 3. Logging
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
``` 