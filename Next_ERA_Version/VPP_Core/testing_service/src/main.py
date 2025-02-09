from fastapi import FastAPI
from src.api.routes import tests

app = FastAPI(
    title="VPP Testing Service",
    description="Service for managing and executing tests for VPP components",
    version="0.1.0"
)

# Include routers
app.include_router(tests.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {
        "service": "VPP Testing Service",
        "version": "0.1.0",
        "status": "running"
    } 