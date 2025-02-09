from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from typing import List, Dict
import asyncio
import json
from datetime import datetime
import os
from pathlib import Path

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Type definitions
class LoadProfileData:
    def __init__(self, base_load: List[float], with_dr: List[float]):
        self.timestamp = datetime.now().timestamp() * 1000  # JavaScript timestamp
        self.base_load = base_load
        self.with_dr = with_dr

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "baseLoad": self.base_load,
            "withDR": self.with_dr
        }

# Global data store
load_profile_data = None

def load_csv_data() -> LoadProfileData:
    try:
        # Adjust path as needed
        csv_path = Path(__file__).parent.parent / 'data' / 'Saudi_Demand_by_Group_and_Region.csv'
        df = pd.read_csv(csv_path)
        
        # Get base load from CSV
        base_load = df['Profile'].tolist()
        
        # Calculate DR impact (10% reduction during peak hours)
        with_dr = []
        for hour, value in enumerate(base_load):
            time_of_day = hour % 24
            is_peak_hour = 9 <= time_of_day <= 21
            dr_value = value * 0.9 if is_peak_hour else value
            with_dr.append(dr_value)
        
        return LoadProfileData(base_load, with_dr)
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return generate_random_data()

def generate_random_data() -> LoadProfileData:
    base_load = [np.random.random() * 40000 for _ in range(8760)]
    with_dr = [np.random.random() * 35000 for _ in range(8760)]
    return LoadProfileData(base_load, with_dr)

@app.on_event("startup")
async def startup_event():
    global load_profile_data
    load_profile_data = load_csv_data()

@app.get("/api/load-profile")
async def get_load_profile():
    global load_profile_data
    if load_profile_data is None:
        load_profile_data = load_csv_data()
    return load_profile_data.to_dict()

# Store active WebSocket connections
active_connections: List[WebSocket] = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send initial data
        if load_profile_data:
            await websocket.send_json(load_profile_data.to_dict())
        
        # Keep connection alive and send updates
        while True:
            # Add small random variations (5%)
            variation = 0.05
            base_variations = np.random.uniform(-variation/2, variation/2, len(load_profile_data.base_load))
            dr_variations = np.random.uniform(-variation/2, variation/2, len(load_profile_data.with_dr))
            
            updated_data = LoadProfileData(
                [val * (1 + var) for val, var in zip(load_profile_data.base_load, base_variations)],
                [val * (1 + var) for val, var in zip(load_profile_data.with_dr, dr_variations)]
            )
            
            await websocket.send_json(updated_data.to_dict())
            await asyncio.sleep(60)  # Update every minute
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        active_connections.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=3001, reload=True) 