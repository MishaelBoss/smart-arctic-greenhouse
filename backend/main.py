from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, SQLModel
from datetime import datetime
import secrets

from database import engine, get_session
from models import Device, Telemetry
from schemas import (
    DeviceCreate, DeviceOut,
    TelemetryIn, TelemetryOut,
    CommandIn
)

FRESH_TIMEOUT_SECONDS = 15

app = FastAPI(title="Greenhouse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)
    print("Database initialized")


# ==================== УСТРОЙСТВА ====================

@app.post("/api/devices", response_model=DeviceOut)
def create_device(payload: DeviceCreate, session: Session = Depends(get_session)):
    device = Device(name=payload.name, api_key=secrets.token_urlsafe(24), connection_type=payload.connection_type)
    session.add(device)
    session.commit()
    session.refresh(device)
    return device


@app.get("/api/devices", response_model=list[DeviceOut])
def list_devices(session: Session = Depends(get_session)):
    return session.exec(select(Device)).all()


@app.delete("/api/devices/{device_id}")
def delete_device(device_id: int,
                  session: Session = Depends(get_session)):
    device = session.get(Device, device_id)
    if not device:
        raise HTTPException(404, "Device not found")
    session.delete(device)
    session.commit()
    return {"ok": True}


# ==================== ПРИЁМ ДАННЫХ ОТ ESP32 ====================

@app.post("/api/telemetry")
def ingest_telemetry(
    data: TelemetryIn,
    x_api_key: str = Header(...),
    session: Session = Depends(get_session),
):
    device = session.exec(
        select(Device).where(Device.api_key == x_api_key)
    ).first()

    if not device:
        raise HTTPException(401, "Invalid API key")

    t = Telemetry(
        device_id=device.id,
        soil1_raw=data.soil1_raw,
        soil1_moisture=data.soil1_moisture,
        soil2_raw=data.soil2_raw,
        soil2_moisture=data.soil2_moisture,
        temperature=data.temperature,
        humidity=data.humidity,
    )
    session.add(t)
    device.last_seen = datetime.utcnow()
    session.add(device)
    session.commit()
    return {"ok": True}


# ==================== ЧТЕНИЕ ДАННЫХ ====================

@app.get("/api/devices/{device_id}/latest")
def get_latest(device_id: int, session: Session = Depends(get_session)):
    q = (
        select(Telemetry)
        .where(Telemetry.device_id == device_id)
        .order_by(Telemetry.timestamp.desc())
        .limit(1)
    )
    t = session.exec(q).first()
    if t is None:
        return None

    age = (datetime.utcnow() - t.timestamp).total_seconds()
    return {
        "soil1_raw": t.soil1_raw,
        "soil1_moisture": t.soil1_moisture,
        "soil2_raw": t.soil2_raw,
        "soil2_moisture": t.soil2_moisture,
        "temperature": t.temperature,
        "humidity": t.humidity,
        "timestamp": t.timestamp,
        "is_fresh": age < FRESH_TIMEOUT_SECONDS,
        "age_seconds": age,
    }


@app.get("/api/devices/{device_id}/history",
         response_model=list[TelemetryOut])
def get_history(device_id: int, limit: int = 100,
                session: Session = Depends(get_session)):
    q = (
        select(Telemetry)
        .where(Telemetry.device_id == device_id)
        .order_by(Telemetry.timestamp.desc())
        .limit(limit)
    )
    return list(reversed(session.exec(q).all()))


# ==================== ОЧЕРЕДЬ КОМАНД ====================

pending_commands: dict[int, list[str]] = {}


@app.post("/api/devices/{device_id}/command")
def send_command(device_id: int, cmd: CommandIn):
    pending_commands.setdefault(device_id, []).append(cmd.action)
    return {"ok": True, "queued": cmd.action}


@app.get("/api/devices/{device_id}/command")
def get_command(
    device_id: int,
    x_api_key: str = Header(...),
    session: Session = Depends(get_session),
):
    device = session.exec(
        select(Device).where(Device.api_key == x_api_key)
    ).first()

    if not device or device.id != device_id:
        raise HTTPException(401, "Invalid API key")

    cmds = pending_commands.pop(device_id, [])
    return {"commands": cmds}