from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class Country(Base):
    __tablename__ = "countries"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    short_name = Column(String(10), unique=True, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now())

class Currency(Base):
    __tablename__ = "currencies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    short_name = Column(String(10), unique=True, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now())

class Airport(Base):
    __tablename__ = "airports"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    iata_code = Column(String(3), unique=True, nullable=False, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now())

class Charge(Base):
    __tablename__ = "charges"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    short_name = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    aliases = relationship("ChargeAlias", back_populates="charge", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('company_id', 'name', name='uix_company_charge_name'),
        UniqueConstraint('company_id', 'short_name', name='uix_company_charge_short_name'),
    )

class ChargeAlias(Base):
    __tablename__ = "charge_aliases"
    
    id = Column(Integer, primary_key=True, index=True)
    charge_id = Column(Integer, ForeignKey("charges.id", ondelete="CASCADE"), nullable=False, index=True)
    alias = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    charge = relationship("Charge", back_populates="aliases")
    
    __table_args__ = (
        UniqueConstraint('charge_id', 'alias', name='uix_charge_alias'),
    )
