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
class UrgencyEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


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
    email = Column(String, unique=True, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


# ================================
# 📅 BOOKING TABLE (NEW - REQUIRED)
# ================================
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    service_name = Column(String, nullable=True)
    scheduled_time = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


# ================================
# 🛠️ WORK ORDER TABLE
# ================================
class WorkOrder(Base):
    __tablename__ = "work_orders"

    # 🆔 Primary ID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 🔗 Foreign Keys (NOW VALID)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # 📌 Core Details
    customer_message = Column(Text, nullable=False)
    category = Column(String, index=True, nullable=False)

    urgency = Column(Enum(UrgencyEnum), nullable=False)
    summary_for_technician = Column(Text, nullable=False)

    # 🤖 AI Structured Output
    ai_metadata = Column(JSON, nullable=True)

    # 💰 Cost Estimation
    estimated_labor_cost = Column(Float, default=0.0)
    estimated_parts_cost = Column(Float, default=0.0)

    bill_of_materials = Column(JSON, nullable=True)

    final_labor_cost = Column(Float, nullable=True)
    final_parts_cost = Column(Float, nullable=True)

    # 💳 Escrow
    escrow_status = Column(
        Enum(EscrowStatusEnum),
        default=EscrowStatusEnum.PENDING,
        nullable=False
    )

    escrow_transaction_id = Column(String, nullable=True)

    # 📸 Proof System
    before_images = Column(JSON, nullable=True)
    after_images = Column(JSON, nullable=True)

    # ⚠️ Dispute
    dispute_reason = Column(Text, nullable=True)
    dispute_status = Column(String, nullable=True)

    # ⏱️ Timeline
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # 🔗 Relationships
    customer = relationship("User", foreign_keys=[customer_id])
    partner = relationship("User", foreign_keys=[partner_id])
    booking = relationship("Booking")

    # 🧠 Computed Properties
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
        return self.escrow_status == EscrowStatusEnum.RELEASED