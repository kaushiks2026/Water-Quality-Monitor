from sqlalchemy import Column, String, DateTime, Boolean, Text
from datetime import datetime, timezone
from backend.app.database.session import Base


def utc_now():
    return datetime.now(timezone.utc)


class Device(Base):
    """
    Represents an IoT device (e.g., ESP32 node or Simulator) registered in the system.
    """
    __tablename__ = "devices"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    location = Column(String(150), nullable=True, default="Water Reservoir / Testing Tank")
    is_simulator = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    notes = Column(Text, nullable=True)
