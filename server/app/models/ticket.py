from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class DistressTicket(Base):
    """
    Authoritative server-side distress ticket stored in SQLite.
    Segregated from client-side IndexedDB local packets.
    """
    __tablename__ = "distress_tickets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Unique client-generated packet UUID for idempotent synchronization & de-duplication
    client_packet_id = Column(String(64), unique=True, index=True, nullable=False)
    packet_tag = Column(String(32), nullable=True)  # e.g., 'PKT-9440'

    # Emergency categorization: medical, flood, supplies, hazard
    category = Column(String(32), index=True, nullable=False, default="medical")
    title = Column(String(128), nullable=False)
    telugu_title = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)

    # Location Telemetry:
    # 1. Landmark is MANDATORY so citizens can report distress without GPS.
    # 2. GPS latitude and longitude are strictly OPTIONAL.
    landmark = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    gps_accuracy_meters = Column(Float, nullable=True)

    # Caller Privacy: Redacted for public triage views; unmasked only for authenticated responders
    contact_phone = Column(String(32), nullable=True)

    # Triage Urgency: red (trauma/life threat), amber (rations/vulnerable), blue (infrastructure/roads)
    urgency_tier = Column(String(16), index=True, default="red")

    # Workflow lifecycle: pending -> claimed -> en_route -> resolved -> cancelled
    status = Column(String(32), index=True, default="pending", nullable=False)

    # Responder attribution & atomic claiming
    assigned_squad = Column(String(64), nullable=True)
    claimed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    claimed_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Data Integrity: Clearly marks demonstration data
    is_simulated = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    claimed_by = relationship("User", back_populates="claimed_tickets")

    def __repr__(self):
        return f"<DistressTicket id={self.id} packet={self.packet_tag} status={self.status} sim={self.is_simulated}>"
