from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, ForeignKey, Index
from datetime import datetime, timezone
from backend.app.database.session import Base


def utc_now():
    return datetime.now(timezone.utc)


class SensorReading(Base):
    """
    Stores timestamped physical or simulated sensor measurements.
    Uninstalled sensors (e.g. Dissolved Oxygen) remain None/NULL.
    """
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(50), ForeignKey("devices.id"), nullable=False, index=True)
    
    # Measured Parameters (NULL if sensor uninstalled/reading unavailable)
    ph = Column(Float, nullable=True)
    turbidity = Column(Float, nullable=True)      # NTU
    temperature = Column(Float, nullable=True)    # °C
    dissolved_oxygen = Column(Float, nullable=True) # mg/L

    # Metadata & Provenance
    is_simulated = Column(Boolean, default=False, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    received_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Risk evaluation cache
    risk_level = Column(String(20), default="SAFE", nullable=False)  # SAFE, WARNING, CRITICAL, UNKNOWN

    # Composite index for rapid historical queries filtered by device and time range
    __table_args__ = (
        Index("ix_device_timestamp", "device_id", "timestamp"),
    )
