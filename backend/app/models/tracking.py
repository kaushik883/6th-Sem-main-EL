from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.models.base import Base

class TrackingEvent(Base):
    __tablename__ = "tracking_events"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True)
    event_time = Column(DateTime, nullable=False, index=True)
    location = Column(String(255), nullable=True)
    status = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), ForeignKey("profiles.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True) # Assuming JSON stored as text or JSON type if we use PostgreSQL specific
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
