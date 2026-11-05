from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.database import Base


class DisasterZone(Base):
    """
    Hyper-local cyclone sector and grid telemetry.
    All records flagged with is_simulated to prevent confusing mock data with live reports.
    """
    __tablename__ = "disaster_zones"

    zone_key = Column(String(32), primary_key=True)  # e.g., 'mvp', 'jalaripeta', 'au_stadium', 'gvmc_school'
    name = Column(String(128), nullable=False)
    telugu_name = Column(String(128), nullable=False)
    vulnerability_tag = Column(String(64), nullable=False)

    # Telemetry indicators matching Stitch UI states
    status = Column(String(64), nullable=False)  # 'CRITICAL SURGE', 'RELIEF PENDING', 'SAFE & OPERATIONAL'
    status_class = Column(String(64), nullable=False)  # Tailwind classes for color pills

    active_sos_count = Column(Integer, default=0, nullable=False)
    deployed_squads = Column(String(64), nullable=False)
    water_level = Column(String(32), nullable=False)

    # Data Integrity Flag
    is_simulated = Column(Boolean, default=True, nullable=False)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<DisasterZone key={self.zone_key} status={self.status} sim={self.is_simulated}>"
