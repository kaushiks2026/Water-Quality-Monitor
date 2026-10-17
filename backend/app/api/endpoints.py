from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timezone


from backend.app.database.session import get_db
from backend.app.config import settings
from backend.app.models.device import Device
from backend.app.models.reading import SensorReading
from backend.app.models.alert import Alert
from backend.app.schemas.sensor import (
    SensorReadingCreate,
    SensorReadingResponse,
    DeviceResponse,
    AlertResponse,
    RiskEvaluationResult
)
from backend.app.services.risk_service import evaluate_water_quality

def utc_now():
    return datetime.now(timezone.utc)


router = APIRouter(tags=["Sensor Readings & IoT Telemetry"])


def verify_device_token(x_device_token: Optional[str] = Header(None)):
    """
    Optional token authentication for IoT nodes.
    If DEVICE_API_KEY is configured in settings and token does not match, reject with 401.
    """
    if settings.DEVICE_API_KEY:
        if not x_device_token or x_device_token != settings.DEVICE_API_KEY:
            raise HTTPException(
                status_code=401,
                detail="Unauthorized: Invalid or missing X-Device-Token header."
            )
    return True


@router.post("/readings", response_model=SensorReadingResponse, status_code=201)
def ingest_reading(
    payload: SensorReadingCreate,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_device_token)
):
    """
    Primary ingestion endpoint for ESP32 and Data Simulator.
    Validates payload, registers device if unseen, evaluates water quality risk rules,
    generates alerts if safety thresholds are exceeded, and stores the reading.
    """
    # 1. Ensure Device exists or register auto-discovery
    device = db.query(Device).filter(Device.id == payload.device_id).first()
    if not device:
        device = Device(
            id=payload.device_id,
            name=f"Device {payload.device_id}",
            is_simulator=payload.is_simulated,
            is_active=True,
            last_seen=utc_now()
        )
        db.add(device)
    else:
        device.last_seen = utc_now()
        device.is_active = True

    # 2. Evaluate Rule-Based Risk & Threshold Violations
    eval_result = evaluate_water_quality(
        ph=payload.ph,
        turbidity=payload.turbidity,
        temperature=payload.temperature,
        dissolved_oxygen=payload.dissolved_oxygen
    )

    # 3. Create Sensor Reading Record
    reading = SensorReading(
        device_id=payload.device_id,
        timestamp=payload.timestamp or utc_now(),
        received_at=utc_now(),
        is_simulated=payload.is_simulated,
        ph=payload.ph,
        turbidity=payload.turbidity,
        temperature=payload.temperature,
        dissolved_oxygen=payload.dissolved_oxygen,
        risk_level=eval_result["overall_status"]
    )
    db.add(reading)

    # 4. Save any generated Alerts
    for alert_data in eval_result["alerts_generated"]:
        alert = Alert(
            device_id=payload.device_id,
            parameter=alert_data["parameter"],
            severity=alert_data["severity"],
            trigger_value=alert_data["trigger_value"],
            threshold_limit=alert_data["threshold_limit"],
            message=alert_data["message"],
            standard_reference=alert_data["standard_reference"],
            timestamp=payload.timestamp or utc_now(),
            is_resolved=False
        )
        db.add(alert)

    db.commit()
    db.refresh(reading)
    return reading


@router.get("/readings/latest", response_model=Optional[SensorReadingResponse])
def get_latest_reading(
    device_id: Optional[str] = Query(None, description="Filter by device identifier"),
    db: Session = Depends(get_db)
):
    """
    Retrieves the most recent sensor reading.
    """
    query = db.query(SensorReading)
    if device_id:
        query = query.filter(SensorReading.device_id == device_id)
    
    latest = query.order_by(desc(SensorReading.timestamp)).first()
    return latest


@router.get("/readings", response_model=List[SensorReadingResponse])
def get_historical_readings(
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    limit: int = Query(50, ge=1, le=500, description="Max readings to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    start_time: Optional[datetime] = Query(None, description="ISO timestamp start filter"),
    end_time: Optional[datetime] = Query(None, description="ISO timestamp end filter"),
    db: Session = Depends(get_db)
):
    """
    Retrieves paginated historical readings with optional timestamp window filtering.
    """
    query = db.query(SensorReading)
    if device_id:
        query = query.filter(SensorReading.device_id == device_id)
    if start_time:
        query = query.filter(SensorReading.timestamp >= start_time)
    if end_time:
        query = query.filter(SensorReading.timestamp <= end_time)

    readings = query.order_by(desc(SensorReading.timestamp)).offset(offset).limit(limit).all()
    return readings


@router.get("/devices", response_model=List[DeviceResponse])
def list_devices(db: Session = Depends(get_db)):
    """
    Returns list of all registered IoT nodes and simulator instances.
    """
    return db.query(Device).all()


@router.get("/alerts", response_model=List[AlertResponse])
def get_recent_alerts(
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retrieves latest safety violations and risk notifications.
    """
    query = db.query(Alert)
    if device_id:
        query = query.filter(Alert.device_id == device_id)
    return query.order_by(desc(Alert.timestamp)).limit(limit).all()


@router.get("/evaluate/latest", response_model=RiskEvaluationResult)
def evaluate_latest(
    device_id: Optional[str] = Query(None, description="Device ID to evaluate"),
    db: Session = Depends(get_db)
):
    """
    Performs full live risk breakdown on the most recent sensor reading.
    """
    query = db.query(SensorReading)
    if device_id:
        query = query.filter(SensorReading.device_id == device_id)
    latest = query.order_by(desc(SensorReading.timestamp)).first()

    if not latest:
        return RiskEvaluationResult(
            overall_status="UNKNOWN",
            summary_message="No readings recorded yet in database.",
            parameters_evaluated={},
            alerts_generated=[]
        )

    eval_result = evaluate_water_quality(
        ph=latest.ph,
        turbidity=latest.turbidity,
        temperature=latest.temperature,
        dissolved_oxygen=latest.dissolved_oxygen
    )
    return RiskEvaluationResult(**eval_result)
