from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """
    Authenticated responder and coordinator entity.
    Enforces role-based permissions (volunteer, admin, dispatcher).
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(128), nullable=True)

    role = Column(String(32), index=True, nullable=False, default="volunteer")
    squad_name = Column(String(64), nullable=True)  # e.g., 'AU Ward Squad #14', 'SDRF Team 04'

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    claimed_tickets = relationship("DistressTicket", back_populates="claimed_by")

    def __repr__(self):
        return f"<User username={self.username} role={self.role} squad={self.squad_name}>"
