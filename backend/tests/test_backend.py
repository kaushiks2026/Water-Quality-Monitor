import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

from backend.app.main import app
from backend.app.database.session import Base, get_db
from backend.app.config import settings
from backend.app.models import Device, SensorReading, Alert
from backend.app.services.risk_service import evaluate_water_quality

# Use in-memory SQLite database specifically isolated for tests
# StaticPool ensures in-memory sqlite shares data across threads in the test runner
from sqlalchemy.pool import StaticPool
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Build schema in memory before each test
    Base.metadata.create_all(bind=engine)
    yield
    # Drop schema after test run
    Base.metadata.drop_all(bind=engine)


# 1. System Health Test
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# 2. Risk Evaluation Unit Tests
def test_risk_evaluation_safe():
    res = evaluate_water_quality(ph=7.2, turbidity=0.6, temperature=24.0, dissolved_oxygen=7.0)
    assert res["overall_status"] == "SAFE"
    assert len(res["alerts_generated"]) == 0
    assert res["parameters_evaluated"]["ph"]["status"] == "NORMAL"
    assert res["parameters_evaluated"]["turbidity"]["status"] == "NORMAL"


def test_risk_evaluation_acidic_warning():
    res = evaluate_water_quality(ph=6.1, turbidity=0.6, temperature=24.0, dissolved_oxygen=None)
    assert res["overall_status"] == "WARNING"
    assert len(res["alerts_generated"]) == 1
    assert res["alerts_generated"][0]["parameter"] == "ph"
    assert res["alerts_generated"][0]["severity"] == "WARNING"


def test_risk_evaluation_turbidity_critical():
    res = evaluate_water_quality(ph=7.4, turbidity=8.5, temperature=24.0, dissolved_oxygen=None)
    assert res["overall_status"] == "CRITICAL"
    assert len(res["alerts_generated"]) == 1
    assert res["alerts_generated"][0]["parameter"] == "turbidity"
    assert res["alerts_generated"][0]["severity"] == "CRITICAL"


# 3. Authentication & Security Tests
def test_ingestion_unauthorized_when_no_token():
    payload = {
        "device_id": "TEST-NODE",
        "ph": 7.0,
        "turbidity": 0.5,
        "temperature": 25.0
    }
    response = client.post("/api/readings", json=payload)
    assert response.status_code == 401
    assert "Unauthorized" in response.json()["detail"]


# 4. Valid Telemetry Ingestion & DB Persistence
def test_ingestion_valid_payload():
    payload = {
        "device_id": "TEST-ESP32",
        "is_simulated": False,
        "ph": 7.45,
        "turbidity": 0.82,
        "temperature": 26.2,
        "dissolved_oxygen": None  # Dissolved oxygen uninstalled
    }
    headers = {"X-Device-Token": settings.DEVICE_API_KEY}
    response = client.post("/api/readings", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["device_id"] == "TEST-ESP32"
    assert data["is_simulated"] is False
    assert data["ph"] == 7.45
    assert data["turbidity"] == 0.82
    assert data["temperature"] == 26.2
    assert data["dissolved_oxygen"] is None
    assert data["risk_level"] == "SAFE"

    # Query latest endpoint
    res_latest = client.get("/api/readings/latest")
    assert res_latest.status_code == 200
    latest_data = res_latest.json()
    assert latest_data["device_id"] == "TEST-ESP32"
    assert latest_data["ph"] == 7.45


# 5. Ingestion with Alert Generation
def test_ingestion_generates_alert_in_db():
    payload = {
        "device_id": "TEST-ESP32",
        "is_simulated": True,
        "ph": 4.5,  # Severe acidic violation
        "turbidity": 12.0,  # Critical turbidity violation
        "temperature": 24.0
    }
    headers = {"X-Device-Token": settings.DEVICE_API_KEY}
    response = client.post("/api/readings", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["risk_level"] == "CRITICAL"

    # Check alert table via API
    alerts_res = client.get("/api/alerts")
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) >= 2  # Both pH and turbidity violations recorded
    params = [a["parameter"] for a in alerts]
    assert "ph" in params
    assert "turbidity" in params


# 6. Physical Plausibility Validation Tests
def test_ingestion_rejects_physically_impossible_ph():
    payload = {
        "device_id": "TEST-NODE",
        "ph": 18.5,  # Impossible pH (> 14)
        "turbidity": 1.0,
        "temperature": 25.0
    }
    headers = {"X-Device-Token": settings.DEVICE_API_KEY}
    response = client.post("/api/readings", json=payload, headers=headers)
    assert response.status_code == 422  # Pydantic validation rejection


def test_ingestion_rejects_negative_turbidity():
    payload = {
        "device_id": "TEST-NODE",
        "ph": 7.0,
        "turbidity": -5.0,  # Impossible turbidity (< 0)
        "temperature": 25.0
    }
    headers = {"X-Device-Token": settings.DEVICE_API_KEY}
    response = client.post("/api/readings", json=payload, headers=headers)
    assert response.status_code == 422
