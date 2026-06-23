from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date, Numeric, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class Quote(Base):
    __tablename__ = "quotes"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_ref = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(20), nullable=False, default='SUBMITTED', index=True)
    rejection_note = Column(Text, nullable=True)
    
    forwarder_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    buyer_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    
    origin_airport_id = Column(Integer, ForeignKey("airports.id"), nullable=False)
    destination_airport_id = Column(Integer, ForeignKey("airports.id"), nullable=False)
    tracking_number = Column(String(100), nullable=False, index=True)
    
    sender_name_address = Column(Text, nullable=True)
    receiver_name_address = Column(Text, nullable=True)
    
    num_packages = Column(Integer, nullable=True)
    gross_weight = Column(Numeric(10, 2), nullable=False)
    volumetric_weight = Column(Numeric(10, 2), nullable=False)
    chargeable_weight = Column(Numeric(10, 2), nullable=False)
    
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)
    
    # Virtual Telemetry Forensics — stores 24 h of E&I sensor readings as JSONB
    telemetry_data = Column(JSONB, nullable=True)

    quote_date = Column(Date, server_default=func.current_date())
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    charges = relationship("QuoteCharge", back_populates="quote", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("forwarder_id != buyer_id", name="check_forwarder_buyer_different"),
    )

class QuoteCharge(Base):
    __tablename__ = "quote_charges"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True)
    
    raw_charge_name = Column(String(255), nullable=False)
    mapped_charge_id = Column(Integer, ForeignKey("charges.id"), nullable=True, index=True)
    mapped_charge_name = Column(String(255), nullable=True)
    
    similarity_score = Column(Numeric(5, 4), nullable=True)
    mapping_tier = Column(String(20), nullable=True, index=True)
    low_confidence = Column(Boolean, default=False)
    
    rate = Column(Numeric(10, 2), nullable=False)
    basis = Column(String(50), nullable=False)
    qty = Column(Numeric(10, 2), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    
    created_at = Column(DateTime, server_default=func.now())

    quote = relationship("Quote", back_populates="charges")
