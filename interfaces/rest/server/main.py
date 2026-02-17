"""
EventFlow REST API Server

A FastAPI-based REST API for EventFlow neuromorphic computing platform.
Provides programmatic access to model validation, execution, and trace analysis.
"""

import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

# EventFlow imports (lazy-loaded to avoid import-time issues)
eventflow_core = None
eventflow_cli = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    # Startup
    global eventflow_core, eventflow_cli
    try:
        import eventflow_core
        import eventflow_cli
        print("EventFlow modules loaded successfully")
    except ImportError as e:
        print(f"Warning: EventFlow modules not available: {e}")

    yield

    # Shutdown
    pass


# Create FastAPI application
app = FastAPI(
    title="EventFlow REST API",
    description="RESTful API for EventFlow neuromorphic computing platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API
class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Response timestamp")
    uptime_seconds: int = Field(..., description="Server uptime in seconds")
    active_jobs: int = Field(0, description="Number of active execution jobs")


class ValidationIssue(BaseModel):
    severity: str = Field(..., description="Issue severity")
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable message")
    location: Optional[Dict[str, Any]] = Field(None, description="Location in document")


class ValidationResponse(BaseModel):
    valid: bool = Field(..., description="Whether validation passed")
    issues: List[ValidationIssue] = Field(default_factory=list, description="Validation issues found")


class ModelSummary(BaseModel):
    id: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Model name")
    version: str = Field(..., description="Model version")
    profile: str = Field(..., description="Neuromorphic profile")
    domain: str = Field(..., description="Application domain")
    created_at: datetime = Field(..., description="Creation timestamp")


class ExecutionRequest(BaseModel):
    model_id: str = Field(..., description="Model to execute")
    backend: str = Field("cpu-sim", description="Execution backend")
    inputs: List[Dict[str, Any]] = Field(..., description="Input data specifications")
    plan_id: Optional[str] = Field(None, description="Pre-computed execution plan")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Execution parameters")


class ExecutionResponse(BaseModel):
    job_id: str = Field(..., description="Execution job identifier")
    status: str = Field(..., description="Execution status")
    traces: List[Dict[str, Any]] = Field(default_factory=list, description="Output traces")
    execution_time_us: int = Field(..., description="Execution time in microseconds")
    error: Optional[str] = Field(None, description="Error message if failed")


# Global state
start_time = datetime.now(timezone.utc)
active_jobs = 0


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="SERVING",
        version="0.1.0",
        timestamp=datetime.now(timezone.utc),
        uptime_seconds=int((datetime.now(timezone.utc) - start_time).total_seconds()),
        active_jobs=active_jobs,
    )


@app.post("/validate/eir", response_model=ValidationResponse)
async def validate_eir(eir_data: Dict[str, Any]):
    """Validate EIR document"""
    if not eventflow_core:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="EventFlow core not available"
        )

    try:
        # Use EventFlow validation logic
        # This is a placeholder - actual implementation would use eventflow_core validators
        issues = []

        # Basic validation checks
        if not isinstance(eir_data, dict):
            issues.append(ValidationIssue(
                severity="ERROR",
                code="INVALID_FORMAT",
                message="EIR must be a JSON object"
            ))

        if "nodes" not in eir_data:
            issues.append(ValidationIssue(
                severity="ERROR",
                code="MISSING_NODES",
                message="EIR must contain 'nodes' field"
            ))

        return ValidationResponse(
            valid=len(issues) == 0,
            issues=issues
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


@app.get("/models", response_model=List[ModelSummary])
async def list_models():
    """List available models"""
    # Placeholder - in real implementation would query model registry
    return []


@app.post("/execute/{model_id}/run", response_model=ExecutionResponse)
async def execute_model(model_id: str, request: ExecutionRequest):
    """Execute a model"""
    global active_jobs

    if not eventflow_cli:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="EventFlow CLI not available"
        )

    try:
        active_jobs += 1

        # Placeholder execution logic
        # In real implementation would use eventflow_cli to execute the model
        import uuid
        job_id = str(uuid.uuid4())

        return ExecutionResponse(
            job_id=job_id,
            status="COMPLETED",
            traces=[],
            execution_time_us=1000,
            error=None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {str(e)}"
        )
    finally:
        active_jobs -= 1


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "EventFlow REST API", "version": "0.1.0"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )