from pydantic import BaseSettings
from typing import List, Optional
from datetime import timedelta

class ServiceConfig(BaseSettings):
    # Service Identity
    SERVICE_NAME: str = "forecasting_service"
    SERVICE_VERSION: str = "1.0.0"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8014  # Updated port number
    
    # Forecasting Configuration
    FORECAST_HORIZON: timedelta = timedelta(hours=24)  # Default 24-hour forecast
    UPDATE_INTERVAL: timedelta = timedelta(minutes=15)  # Update forecasts every 15 minutes
    HISTORY_WINDOW: timedelta = timedelta(days=30)  # Historical data window for training
    
    # Model Configuration
    LOAD_MODEL_TYPE: str = "prophet"  # Options: prophet, lstm, xgboost
    RENEWABLE_MODEL_TYPE: str = "prophet"
    CONTROLLABILITY_MODEL_TYPE: str = "xgboost"
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_CONSUMER_GROUP: str = "forecasting_service"
    KAFKA_TOPICS: List[str] = [
        "vpp.measurements.load",
        "vpp.measurements.renewable",
        "vpp.measurements.controllability",
        "vpp.forecasts.updates"
    ]
    
    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/vpp_forecasting"
    
    # Security
    API_KEY: Optional[str] = None
    JWT_SECRET: Optional[str] = None
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    TRACING_ENABLED: bool = True
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        
settings = ServiceConfig() 