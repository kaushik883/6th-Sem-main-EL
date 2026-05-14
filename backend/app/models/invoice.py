from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date, Numeric, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_number = Column(String(100), unique=True, nullable=False, index=True)
    invoice_date = Column(Date, nullable=False)
    file_path = Column(Text, nullable=False)
    uploaded_at = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())

    charges = relationship("InvoiceCharge", back_populates="invoice", cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceCharge(Base):
    __tablename__ = "invoice_charges"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    
    raw_charge_name = Column(String(255), nullable=False)
    mapped_charge_id = Column(Integer, ForeignKey("charges.id"), nullable=True, index=True)
    mapped_charge_name = Column(String(255), nullable=True)
    
    similarity_score = Column(Numeric(5, 4), nullable=True)
    mapping_tier = Column(String(20), nullable=True)
    low_confidence = Column(Boolean, default=False)
    
    rate = Column(Numeric(10, 2), nullable=False)
    basis = Column(String(50), nullable=False)
    qty = Column(Numeric(10, 2), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    
    created_at = Column(DateTime, server_default=func.now())

    invoice = relationship("Invoice", back_populates="charges")

class Anomaly(Base):
    __tablename__ = "anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_charge_id = Column(Integer, ForeignKey("invoice_charges.id", ondelete="SET NULL"), nullable=True)
    
    flag_type = Column(String(30), nullable=False, index=True)
    description = Column(Text, nullable=False)
    variance = Column(Numeric(10, 2), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())

    invoice = relationship("Invoice", back_populates="anomalies")
