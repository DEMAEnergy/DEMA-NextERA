from typing import List, Dict, Optional, Type
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.ensemble import GradientBoostingRegressor
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

from ..models.forecast_models import (
    ForecastType,
    ForecastPoint,
    ForecastSeries,
    LoadForecast,
    RenewableForecast,
    ControllabilityForecast,
)
from ...config.settings import settings

class BaseForecaster:
    def __init__(self):
        self.model = None
        self.history: pd.DataFrame = pd.DataFrame()
        
    async def train(self, data: pd.DataFrame):
        raise NotImplementedError
        
    async def predict(self, start_time: datetime, end_time: datetime, resolution: str) -> List[ForecastPoint]:
        raise NotImplementedError

class ProphetForecaster(BaseForecaster):
    def __init__(self):
        super().__init__()
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=True,
            interval_width=0.95
        )
    
    async def train(self, data: pd.DataFrame):
        df = data.rename(columns={"timestamp": "ds", "value": "y"})
        self.model.fit(df)
        
    async def predict(self, start_time: datetime, end_time: datetime, resolution: str) -> List[ForecastPoint]:
        future_dates = pd.date_range(start=start_time, end=end_time, freq=resolution)
        future = pd.DataFrame({"ds": future_dates})
        forecast = self.model.predict(future)
        
        return [
            ForecastPoint(
                timestamp=row.ds,
                value=row.yhat,
                confidence_lower=row.yhat_lower,
                confidence_upper=row.yhat_upper
            )
            for _, row in forecast.iterrows()
        ]

class LSTMForecaster(BaseForecaster):
    def __init__(self, sequence_length: int = 24):
        super().__init__()
        self.sequence_length = sequence_length
        self.model = Sequential([
            LSTM(50, activation='relu', input_shape=(sequence_length, 1)),
            Dense(1)
        ])
        self.model.compile(optimizer='adam', loss='mse')
        
    async def train(self, data: pd.DataFrame):
        values = data['value'].values
        X, y = self._prepare_sequences(values)
        self.model.fit(X, y, epochs=50, batch_size=32, verbose=0)
        
    async def predict(self, start_time: datetime, end_time: datetime, resolution: str) -> List[ForecastPoint]:
        # Implementation for LSTM predictions
        pass

class XGBoostForecaster(BaseForecaster):
    def __init__(self):
        super().__init__()
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=3
        )
        
    async def train(self, data: pd.DataFrame):
        # Prepare features (time-based, weather, etc.)
        X = self._prepare_features(data)
        y = data['value']
        self.model.fit(X, y)
        
    async def predict(self, start_time: datetime, end_time: datetime, resolution: str) -> List[ForecastPoint]:
        # Implementation for XGBoost predictions
        pass

class ForecastingService:
    def __init__(self):
        self.forecasters: Dict[ForecastType, Dict[str, Type[BaseForecaster]]] = {
            ForecastType.LOAD: {
                "prophet": ProphetForecaster,
                "lstm": LSTMForecaster,
                "xgboost": XGBoostForecaster
            },
            ForecastType.RENEWABLE: {
                "prophet": ProphetForecaster,
                "lstm": LSTMForecaster,
                "xgboost": XGBoostForecaster
            },
            ForecastType.CONTROLLABILITY: {
                "xgboost": XGBoostForecaster
            }
        }
        
        self.active_forecasters: Dict[ForecastType, BaseForecaster] = {}
        self._initialize_forecasters()
        
    def _initialize_forecasters(self):
        self.active_forecasters[ForecastType.LOAD] = self.forecasters[ForecastType.LOAD][settings.LOAD_MODEL_TYPE]()
        self.active_forecasters[ForecastType.RENEWABLE] = self.forecasters[ForecastType.RENEWABLE][settings.RENEWABLE_MODEL_TYPE]()
        self.active_forecasters[ForecastType.CONTROLLABILITY] = self.forecasters[ForecastType.CONTROLLABILITY][settings.CONTROLLABILITY_MODEL_TYPE]()
    
    async def update_historical_data(self, forecast_type: ForecastType, data: pd.DataFrame):
        """Update historical data and retrain the model if necessary"""
        forecaster = self.active_forecasters[forecast_type]
        await forecaster.train(data)
    
    async def generate_forecast(
        self,
        forecast_type: ForecastType,
        start_time: datetime,
        end_time: datetime,
        resolution: str,
        parameters: Optional[Dict] = None
    ) -> ForecastSeries:
        """Generate a forecast for the specified type and time range"""
        forecaster = self.active_forecasters[forecast_type]
        forecast_points = await forecaster.predict(start_time, end_time, resolution)
        
        # Create appropriate forecast series based on type
        if forecast_type == ForecastType.LOAD:
            return LoadForecast(
                forecast_type=forecast_type,
                start_time=start_time,
                end_time=end_time,
                resolution=resolution,
                points=forecast_points,
                location_id=parameters.get("location_id") if parameters else None,
                customer_segment=parameters.get("customer_segment") if parameters else None
            )
        elif forecast_type == ForecastType.RENEWABLE:
            return RenewableForecast(
                forecast_type=forecast_type,
                start_time=start_time,
                end_time=end_time,
                resolution=resolution,
                points=forecast_points,
                source_type=parameters.get("source_type", "solar") if parameters else "solar",
                location_id=parameters.get("location_id") if parameters else None,
                capacity=parameters.get("capacity") if parameters else None
            )
        else:  # ForecastType.CONTROLLABILITY
            return ControllabilityForecast(
                forecast_type=forecast_type,
                start_time=start_time,
                end_time=end_time,
                resolution=resolution,
                points=forecast_points,
                resource_id=parameters["resource_id"],
                min_power=parameters.get("min_power", []),
                max_power=parameters.get("max_power", []),
                response_time=parameters.get("response_time"),
                cost_function=parameters.get("cost_function")
            ) 