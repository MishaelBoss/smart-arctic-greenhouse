from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DeviceCreate(BaseModel):
    name: str
    connection_type: str = "wifi" 


class DeviceOut(BaseModel):
    id: int
    name: str
    api_key: str
    last_seen: Optional[datetime] = None
    connection_type: str 
    class Config:
        from_attributes = True


class TelemetryIn(BaseModel):
    soil1_raw: int
    soil1_moisture: float
    soil2_raw: int
    soil2_moisture: float
    temperature: Optional[float] = None
    humidity: Optional[float] = None


class TelemetryOut(BaseModel):
    soil1_raw: int
    soil1_moisture: float
    soil2_raw: int
    soil2_moisture: float
    temperature: Optional[float]
    humidity: Optional[float]
    timestamp: datetime
    is_fresh: bool = True 
    age_seconds: float = 0.0 
    class Config:
        from_attributes = True


class CommandIn(BaseModel):
    action: str