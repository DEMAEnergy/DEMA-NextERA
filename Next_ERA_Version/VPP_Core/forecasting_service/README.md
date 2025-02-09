# VPP Forecasting Service

A microservice component of the Virtual Power Plant (VPP) Core system that provides forecasting capabilities for load, renewable generation, and controllability ranges.

## Features

- **Load Forecasting**: Predicts future load consumption patterns
- **Renewable Generation Forecasting**: Forecasts renewable energy generation (solar, wind, etc.)
- **Controllability Forecasting**: Predicts available flexibility and controllability ranges
- **Multiple Model Support**: Implements various forecasting algorithms (Prophet, LSTM, XGBoost)
- **Real-time Updates**: Continuously updates forecasts with new data
- **Batch Processing**: Supports batch forecast generation
- **API-First Design**: RESTful API with OpenAPI documentation
- **Monitoring**: Prometheus metrics integration

## API Endpoints

### Forecast Generation

- `POST /api/v1/forecasts/{forecast_type}`: Generate a forecast
- `POST /api/v1/forecasts/{forecast_type}/batch`: Generate multiple forecasts
- `GET /api/v1/forecasts/{forecast_type}/latest`: Get latest forecast
- `POST /api/v1/forecasts/{forecast_type}/update-data`: Update historical data

### Monitoring

- `GET /health`: Service health check
- `GET /metrics`: Prometheus metrics

## Configuration

Configuration is managed through environment variables or `.env` file:

```env
# Service Identity
SERVICE_NAME=forecasting_service
SERVICE_VERSION=1.0.0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Forecasting Configuration
FORECAST_HORIZON=24  # hours
UPDATE_INTERVAL=15  # minutes
HISTORY_WINDOW=30  # days

# Model Configuration
LOAD_MODEL_TYPE=prophet
RENEWABLE_MODEL_TYPE=prophet
CONTROLLABILITY_MODEL_TYPE=xgboost

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_CONSUMER_GROUP=forecasting_service

# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@localhost/vpp_forecasting
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Service

### Local Development

```bash
python src/main.py
```

### Docker

```bash
docker build -t vpp-forecasting-service .
docker run -p 8000:8000 vpp-forecasting-service
```

## Development

### Project Structure

```
forecasting_service/
├── src/
│   ├── api/                 # API endpoints
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
├── Dockerfile             # Container definition
├── requirements.txt       # Python dependencies
└── README.md             # Documentation
```

### Testing

```bash
pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[MIT License](LICENSE) 