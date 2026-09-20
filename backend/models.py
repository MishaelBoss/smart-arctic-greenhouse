from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class Device(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    api_key: str = Field(index=True, unique=True)
    connection_type: str = Field(default="wifi")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: Optional[datetime] = None


class Telemetry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: int = Field(foreign_key="device.id", index=True)

    # Датчики почвы
    soil1_raw: int = 0
    soil1_moisture: float = 0.0
    soil2_raw: int = 0
    soil2_moisture: float = 0.0

    # Климат
    temperature: Optional[float] = None
    humidity: Optional[float] = None

    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)