from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, ForeignKey, Text
from datetime import datetime, timezone
from backend.app.database.session import Base


def utc_now():
    return datetime.now(timezone.utc)


class Alert(Base):
    """
    Records rule-based water-quality threshold exceedances and safety violations.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(50), ForeignKey("devices.id"), nullable=False, index=True)
    parameter = Column(String(50), nullable=False)   # "ph", "turbidity", "temperature", "dissolved_oxygen"
    severity = Column(String(20), nullable=False)    # "WARNING", "CRITICAL"
    trigger_value = Column(Float, nullable=True)     # The observed numeric value
    threshold_limit = Column(String(50), nullable=False) # e.g. "6.5 - 8.5" or "> 5.0 NTU"
    message = Column(Text, nullable=False)           # Explanation of risk
    standard_reference = Column(String(100), default="BIS 10500:2012 / WHO", nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    is_resolved = Column(Boolean, default=False, nullable=False)
