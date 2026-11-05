from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., example="operational")
    project: str = Field(..., example="TyphoonLink Disaster Response Engine")
    version: str = Field(..., example="1.0.0")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    database_connected: bool = True
    notice: str = Field(
        default="[DEMONSTRATION PLATFORM] All seeded zone metrics and telemetry are simulated."
    )


class APIResponse(BaseModel):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Any] = None
    is_simulated_data: bool = True
