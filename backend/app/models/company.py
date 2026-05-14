from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.models.base import Base

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    short_name = Column(String(50), unique=True, nullable=False)
    type = Column(String(20), nullable=False, index=True)
    address_line1 = Column(Text, nullable=True)
    address_line2 = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    zipcode = Column(String(20), nullable=True)
    country_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
