from fastapi import APIRouter, HTTPException, Depends
from typing import List
import uuid
from datetime import datetime, timedelta

from ...core.models.forecast_models import (
    ForecastType,
    ForecastRequest,
    ForecastResponse,
    ForecastSeries
)
from ...core.services.forecasting_service import ForecastingService
from ...config.settings import settings

router = APIRouter(prefix="/api/v1/forecasts", tags=["forecasts"])
forecasting_service = ForecastingService()

@router.post("/{forecast_type}", response_model=ForecastResponse)
async def generate_forecast(
    forecast_type: ForecastType,
    request: ForecastRequest
) -> ForecastResponse:
    """Generate a forecast for the specified type and parameters"""
    try:
        forecast = await forecasting_service.generate_forecast(
            forecast_type=forecast_type,
            start_time=request.start_time,
            end_time=request.end_time,
            resolution=request.resolution,
            parameters=request.parameters
        )
        
        return ForecastResponse(
            request_id=str(uuid.uuid4()),
            forecast=forecast
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{forecast_type}/batch", response_model=List[ForecastResponse])
async def generate_batch_forecasts(
    forecast_type: ForecastType,
    requests: List[ForecastRequest]
) -> List[ForecastResponse]:
    """Generate multiple forecasts in batch"""
    responses = []
    for request in requests:
        try:
            forecast = await forecasting_service.generate_forecast(
                forecast_type=forecast_type,
                start_time=request.start_time,
                end_time=request.end_time,
                resolution=request.resolution,
                parameters=request.parameters
            )
            
            responses.append(ForecastResponse(
                request_id=str(uuid.uuid4()),
                forecast=forecast
            ))
        except Exception as e:
            responses.append(ForecastResponse(
                request_id=str(uuid.uuid4()),
                forecast=None,
                status="error",
                message=str(e)
            ))
    
    return responses

@router.get("/{forecast_type}/latest", response_model=ForecastResponse)
async def get_latest_forecast(
    forecast_type: ForecastType,
    horizon: int = 24,  # hours
    resolution: str = "15min"
) -> ForecastResponse:
    """Get the latest forecast for the specified type"""
    now = datetime.utcnow()
    request = ForecastRequest(
        forecast_type=forecast_type,
        start_time=now,
        end_time=now + timedelta(hours=horizon),
        resolution=resolution
    )
    
    try:
        forecast = await forecasting_service.generate_forecast(
            forecast_type=forecast_type,
            start_time=request.start_time,
            end_time=request.end_time,
            resolution=request.resolution
        )
        
        return ForecastResponse(
            request_id=str(uuid.uuid4()),
            forecast=forecast
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{forecast_type}/update-data")
async def update_historical_data(
    forecast_type: ForecastType,
    data: List[dict]  # List of timestamp-value pairs
):
    """Update historical data for the forecasting models"""
    try:
        import pandas as pd
        df = pd.DataFrame(data)
        await forecasting_service.update_historical_data(forecast_type, df)
        return {"status": "success", "message": "Historical data updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 