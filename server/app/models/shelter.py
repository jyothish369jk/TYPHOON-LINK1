from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.database import Base


class RefugeShelter(Base):
    """
    Verified safe point and refuge shelter directory.
    All records explicitly carry is_simulated flag.
    """
    __tablename__ = "refuge_shelters"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    telugu_name = Column(String(128), nullable=False)
    zone_key = Column(String(32), index=True, nullable=False)
    landmark = Column(String(255), nullable=False)

    capacity = Column(Integer, default=500, nullable=False)
    current_occupancy = Column(Integer, default=0, nullable=False)

    # Operational status checks
    is_operational = Column(Boolean, default=True, nullable=False)
    has_power_generator = Column(Boolean, default=True, nullable=False)
    has_potable_water = Column(Boolean, default=True, nullable=False)
    has_medical_unit = Column(Boolean, default=False, nullable=False)

    # Data Integrity Flag
    is_simulated = Column(Boolean, default=True, nullable=False)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<RefugeShelter name={self.name} occupancy={self.current_occupancy}/{self.capacity} sim={self.is_simulated}>"
