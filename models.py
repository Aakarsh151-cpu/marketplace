from sqlalchemy import Column, String, Float, Text, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime

from database import Base


# ================================
# 🔐 ENUMS
# ================================
class UserRole(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    TECHNICIAN = "TECHNICIAN"
    ADMIN = "ADMIN"


class UrgencyEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class WorkOrderStatusEnum(str, enum.Enum):
    REQUESTED = "REQUESTED"
    ASSIGNED = "ASSIGNED"
    EN_ROUTE = "EN_ROUTE"
    ARRIVED = "ARRIVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class EscrowStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    LOCKED = "LOCKED"
    DISPUTED = "DISPUTED"
    RELEASED = "RELEASED"


# ================================
# 👤 USER TABLE (NEW - REQUIRED)
# ================================
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)


# ================================
# 📅 BOOKING TABLE (NEW - REQUIRED)
# ================================
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    service_name = Column(String, nullable=False)
    scheduled_time = Column(DateTime, nullable=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)


# ================================
# 🛠️ WORK ORDER TABLE
# ================================
class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    technician_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    customer_message = Column(Text, nullable=False)
    category = Column(String, index=True, nullable=False)
    urgency = Column(Enum(UrgencyEnum), nullable=False)
    summary_for_technician = Column(Text, nullable=False)

    status = Column(Enum(WorkOrderStatusEnum), default=WorkOrderStatusEnum.REQUESTED, nullable=False)

    ai_metadata = Column(JSON, nullable=True)

    estimated_labor_cost = Column(Float, default=0.0)
    estimated_parts_cost = Column(Float, default=0.0)
    final_labor_cost = Column(Float, nullable=True)
    final_parts_cost = Column(Float, nullable=True)

    bill_of_materials = Column(JSON, nullable=True)

    escrow_status = Column(
        Enum(EscrowStatusEnum),
        default=EscrowStatusEnum.PENDING,
        nullable=False
    )

    escrow_transaction_id = Column(String, nullable=True)

    before_images = Column(JSON, nullable=True)
    after_images = Column(JSON, nullable=True)

    dispute_reason = Column(Text, nullable=True)
    dispute_status = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    customer = relationship("User", foreign_keys=[customer_id])
    technician = relationship("User", foreign_keys=[technician_id])
    booking = relationship("Booking")

    @property
    def total_estimated_cost(self):
        return (self.estimated_labor_cost or 0) + (self.estimated_parts_cost or 0)

    @property
    def total_final_cost(self):
        return (self.final_labor_cost or 0) + (self.final_parts_cost or 0)

    @property
    def is_paid(self):
        return self.escrow_status == EscrowStatusEnum.LOCKED

    @property
    def is_completed(self):
        return self.status == WorkOrderStatusEnum.COMPLETED
