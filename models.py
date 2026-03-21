from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum
from database import Base

class RoleEnum(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    PARTNER = "PARTNER"

class UrgencyEnum(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    ROUTINE = "ROUTINE"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String(15), unique=True, index=True, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Store GPS for location-based dispatch
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    
    bookings = relationship("Booking", back_populates="customer", foreign_keys='Booking.customer_id')
    created_at = Column(DateTime, default=datetime.utcnow)

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    partner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    category = Column(String, index=True, nullable=False) 
    urgency = Column(Enum(UrgencyEnum), nullable=False)
    
    # The exact JSON brain dump from the Ghost Assistant
    ai_diagnostic = Column(JSON, nullable=False) 
    
    status = Column(String, default="SEARCHING_FOR_PARTNER") 
    final_price = Column(Float, nullable=True) 
    
    customer = relationship("User", foreign_keys=[customer_id])
    created_at = Column(DateTime, default=datetime.utcnow)