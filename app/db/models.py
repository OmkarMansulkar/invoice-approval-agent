"""
Database schema.

Invoice (1) --- (many) LineItem
Invoice (1) --- (1)    Approval
Invoice (1) --- (many) AuditLog
"""
import datetime
import enum

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class InvoiceStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    vendor_name = Column(String, nullable=False)
    invoice_number = Column(String, nullable=True)
    invoice_date = Column(String, nullable=True)  # kept as string: source data is inconsistent
    category = Column(String, nullable=True)
    total_amount = Column(Float, nullable=False, default=0.0)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.PENDING, nullable=False)
    raw_text = Column(Text, nullable=True)  # original input, for traceability
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    line_items = relationship("LineItem", back_populates="invoice", cascade="all, delete-orphan")
    approval = relationship("Approval", back_populates="invoice", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="invoice", cascade="all, delete-orphan")


class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    description = Column(String, nullable=False)
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, default=0.0)
    amount = Column(Float, default=0.0)

    invoice = relationship("Invoice", back_populates="line_items")


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), unique=True, nullable=False)
    decision = Column(Enum(InvoiceStatus), nullable=False)
    reason = Column(Text, nullable=True)       # human-readable summary of rule violations, if any
    decided_by = Column(String, default="approver_agent")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    invoice = relationship("Invoice", back_populates="approval")


class AuditLog(Base):
    """Every agent step writes one row here -- gives you a real trace to show in the interview."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    step = Column(String, nullable=False)      # e.g. "extractor", "validator", "approver"
    detail = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    invoice = relationship("Invoice", back_populates="audit_logs")
