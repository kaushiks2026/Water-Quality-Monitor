from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc)


class SensorReadingCreate(BaseModel):
    """
    Schema for receiving incoming sensor readings from ESP32 or Simulator.
    Validates physical plausibility and formatting.
    """
    device_id: str = Field(..., min_length=2, max_length=50, description="Unique identifier of ESP32 or simulator node")
    timestamp: Optional[datetime] = Field(default_factory=utc_now, description="Reading timestamp in UTC")
    is_simulated: bool = Field(default=False, description="Flag indicating whether data is simulated or genuine physical sensor")

    # Physical Sensor readings (Optional - can be None/null if sensor uninstalled)
    ph: Optional[float] = Field(None, description="pH level (typically 0.0 to 14.0)")
    turbidity: Optional[float] = Field(None, description="Turbidity in Nephelometric Turbidity Units (NTU)")
    temperature: Optional[float] = Field(None, description="Water temperature in degrees Celsius (°C)")
    dissolved_oxygen: Optional[float] = Field(None, description="Dissolved Oxygen (DO) in milligrams per liter (mg/L)")

    # Validation of Physical Plausibility (guards against sensor malfunctions, electrical shorts, or broken wiring)
    @field_validator("ph")
    @classmethod
    def validate_ph(cls, v):
        if v is not None:
            if v < 0.0 or v > 14.0:
                raise ValueError("pH must be physically plausible between 0.0 and 14.0")
        return v

    @field_validator("turbidity")
    @classmethod
    def validate_turbidity(cls, v):
        if v is not None:
            if v < 0.0 or v > 3000.0:
                raise ValueError("Turbidity must be non-negative and physically plausible (0 to 3000 NTU)")
        return v

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v):
        if v is not None:
            if v < -10.0 or v > 100.0:
                raise ValueError("Water temperature must be between -10.0°C and 100.0°C")
        return v

    @field_validator("dissolved_oxygen")
    @classmethod
    def validate_do(cls, v):
        if v is not None:
            if v < 0.0 or v > 30.0:
                raise ValueError("Dissolved Oxygen must be non-negative and physically plausible (0 to 30 mg/L)")
        return v


class SensorReadingResponse(BaseModel):
    """
    Schema for outputting stored sensor readings.
    """
    id: int
    device_id: str
    timestamp: datetime
    received_at: datetime
    is_simulated: bool
    ph: Optional[float] = None
    turbidity: Optional[float] = None
    temperature: Optional[float] = None
    dissolved_oxygen: Optional[float] = None
    risk_level: str

    model_config = ConfigDict(from_attributes=True)


class DeviceResponse(BaseModel):
    id: str
    name: str
    location: Optional[str]
    is_simulator: bool
    is_active: bool
    last_seen: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertResponse(BaseModel):
    id: int
    device_id: str
    parameter: str
    severity: str
    trigger_value: Optional[float]
    threshold_limit: str
    message: str
    standard_reference: str
    timestamp: datetime
    is_resolved: bool

    model_config = ConfigDict(from_attributes=True)



class RiskEvaluationResult(BaseModel):
    overall_status: str  # "SAFE", "WARNING", "CRITICAL", "UNKNOWN"
    summary_message: str
    parameters_evaluated: dict
    alerts_generated: List[dict]
