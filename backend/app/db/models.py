from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from .base import Base

# --- System Metadata ---
class SystemMetadata(Base):
    __tablename__ = "system_metadata"
    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

# --- Structured Data Entities ---
class Customer(Base):
    __tablename__ = "customers"
    customer_id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_city: Mapped[str] = mapped_column(String)
    customer_state: Mapped[str] = mapped_column(String)
    customer_zip_code_prefix: Mapped[str] = mapped_column(String)
    customer_region: Mapped[str] = mapped_column(String)
    customer_name: Mapped[str] = mapped_column(String)
    customer_email: Mapped[str] = mapped_column(String)
    customer_phone: Mapped[str] = mapped_column(String)

class Merchant(Base):
    __tablename__ = "merchants"
    merchant_id: Mapped[str] = mapped_column(String, primary_key=True)
    seller_city: Mapped[str] = mapped_column(String)
    seller_state: Mapped[str] = mapped_column(String)
    seller_zip_code_prefix: Mapped[str] = mapped_column(String)
    merchant_region: Mapped[str] = mapped_column(String)
    merchant_name: Mapped[str] = mapped_column(String)
    merchant_email: Mapped[str] = mapped_column(String)
    merchant_phone: Mapped[str] = mapped_column(String)

class Order(Base):
    __tablename__ = "orders"
    order_id: Mapped[str] = mapped_column(String, primary_key=True)
    order_status: Mapped[str] = mapped_column(String)
    order_purchase_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    order_approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    order_delivered_carrier_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    order_delivered_customer_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    order_estimated_delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delivery_delay_days: Mapped[Optional[float]] = mapped_column(Float)
    purchase_to_delivery_days: Mapped[Optional[float]] = mapped_column(Float)
    derived_delivery_state: Mapped[str] = mapped_column(String)
    order_channel: Mapped[str] = mapped_column(String)

class Transaction(Base):
    __tablename__ = "transactions"
    transaction_id: Mapped[str] = mapped_column(String, primary_key=True)
    payment_type: Mapped[str] = mapped_column(String)
    payment_installments: Mapped[int] = mapped_column(Integer)
    payment_value: Mapped[float] = mapped_column(Float)
    payment_total: Mapped[float] = mapped_column(Float)
    payment_count: Mapped[int] = mapped_column(Integer)
    transaction_status: Mapped[str] = mapped_column(String)
    authorization_status: Mapped[str] = mapped_column(String)

class Delivery(Base):
    __tablename__ = "deliveries"
    delivery_id: Mapped[str] = mapped_column(String, primary_key=True)
    order_id: Mapped[str] = mapped_column(String, ForeignKey("orders.order_id"))
    order_delivered_carrier_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    order_delivered_customer_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    order_estimated_delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delivery_delay_days: Mapped[Optional[float]] = mapped_column(Float)
    delivery_state: Mapped[str] = mapped_column(String)
    tracking_id: Mapped[str] = mapped_column(String)
    carrier_name: Mapped[str] = mapped_column(String)

class Dispute(Base):
    __tablename__ = "disputes"
    dispute_id: Mapped[str] = mapped_column(String, primary_key=True)
    transaction_id: Mapped[str] = mapped_column(String, ForeignKey("transactions.transaction_id"))
    canonical_order_id: Mapped[str] = mapped_column(String, ForeignKey("orders.order_id"))
    dispute_type: Mapped[str] = mapped_column(String)
    dispute_reason: Mapped[str] = mapped_column(String)
    dispute_amount: Mapped[float] = mapped_column(Float)
    dispute_opened_at: Mapped[datetime] = mapped_column(DateTime)
    dispute_status: Mapped[str] = mapped_column(String)
    claim: Mapped[str] = mapped_column(Text)

# --- Policy Entities (Parent/Child Chunking) ---
class PolicyDocument(Base):
    __tablename__ = "policy_documents"
    policy_id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    source_file: Mapped[str] = mapped_column(String)
    version: Mapped[Optional[str]] = mapped_column(String)

class PolicyParentChunk(Base):
    __tablename__ = "policy_parent_chunks"
    parent_chunk_id: Mapped[str] = mapped_column(String, primary_key=True)
    policy_id: Mapped[str] = mapped_column(String, ForeignKey("policy_documents.policy_id"))
    content: Mapped[str] = mapped_column(Text)
    page: Mapped[Optional[int]] = mapped_column(Integer)

class PolicyChildChunk(Base):
    __tablename__ = "policy_child_chunks"
    child_chunk_id: Mapped[str] = mapped_column(String, primary_key=True)
    parent_chunk_id: Mapped[str] = mapped_column(String, ForeignKey("policy_parent_chunks.parent_chunk_id"))
    policy_id: Mapped[str] = mapped_column(String, ForeignKey("policy_documents.policy_id"))
    content: Mapped[str] = mapped_column(Text)
    # BAAI/bge-small-en-v1.5 has 384 dimensions
    embedding: Mapped[list[float]] = mapped_column(Vector(384))
