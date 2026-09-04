from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Text, JSON
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
    customer_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("customers.customer_id"))
    merchant_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("merchants.merchant_id"))
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
    customer = relationship("Customer")
    merchant = relationship("Merchant")

class Transaction(Base):
    __tablename__ = "transactions"
    transaction_id: Mapped[str] = mapped_column(String, primary_key=True)
    order_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("orders.order_id"))
    payment_type: Mapped[str] = mapped_column(String)
    payment_installments: Mapped[int] = mapped_column(Integer)
    payment_value: Mapped[float] = mapped_column(Float)
    payment_total: Mapped[float] = mapped_column(Float)
    payment_count: Mapped[int] = mapped_column(Integer)
    transaction_status: Mapped[str] = mapped_column(String)
    authorization_status: Mapped[str] = mapped_column(String)
    order = relationship("Order")

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
    # models/gemini-embedding-001 has 768 dimensions
    embedding: Mapped[list[float]] = mapped_column(Vector(768))

# --- Phase 5: Decision & Review Entities ---
class DecisionArtifactModel(Base):
    __tablename__ = "decision_artifacts"
    decision_artifact_id: Mapped[str] = mapped_column(String, primary_key=True)
    dispute_id: Mapped[str] = mapped_column(String, ForeignKey("disputes.dispute_id"))
    
    decision: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    case_strength: Mapped[float] = mapped_column(Float)
    success_likelihood: Mapped[float] = mapped_column(Float)
    
    recoverable_amount: Mapped[float] = mapped_column(Float)
    expected_recovery: Mapped[float] = mapped_column(Float)
    estimated_operational_cost: Mapped[float] = mapped_column(Float)
    net_expected_value: Mapped[float] = mapped_column(Float)

    token_usage: Mapped[dict] = mapped_column(JSON)
    token_cost: Mapped[dict] = mapped_column(JSON)
    
    reason_codes: Mapped[list] = mapped_column(JSON)
    key_evidence: Mapped[list] = mapped_column(JSON)
    supporting_evidence: Mapped[list] = mapped_column(JSON)
    contradicting_evidence: Mapped[list] = mapped_column(JSON)
    missing_evidence: Mapped[list] = mapped_column(JSON)
    risk_flags: Mapped[list] = mapped_column(JSON)
    
    deadline: Mapped[str] = mapped_column(String, nullable=True)
    deadline_risk: Mapped[str] = mapped_column(String)
    next_action: Mapped[str] = mapped_column(String)
    rationale: Mapped[str] = mapped_column(String)
    
    workflow_status: Mapped[str] = mapped_column(String)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class HumanReviewModel(Base):
    __tablename__ = "human_reviews"
    review_id: Mapped[str] = mapped_column(String, primary_key=True)
    decision_artifact_id: Mapped[str] = mapped_column(String, ForeignKey("decision_artifacts.decision_artifact_id"))
    dispute_id: Mapped[str] = mapped_column(String, ForeignKey("disputes.dispute_id"))
    
    ai_recommendation: Mapped[dict] = mapped_column(JSON)
    ai_confidence: Mapped[float] = mapped_column(Float)
    ai_explanation: Mapped[dict] = mapped_column(JSON)
    
    human_action: Mapped[str] = mapped_column(String)
    human_reason: Mapped[Optional[str]] = mapped_column(String)
    
    edited_decision: Mapped[Optional[str]] = mapped_column(String)
    edited_response: Mapped[Optional[str]] = mapped_column(String)
    
    reviewer_id: Mapped[str] = mapped_column(String)
    review_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    previous_state: Mapped[str] = mapped_column(String)
    new_state: Mapped[str] = mapped_column(String)

# --- Cross-Phase LLM Token Accounting ---
class LlmUsageRecordModel(Base):
    """
    One row per LLM invocation, scoped to a dispute.
    Aggregated for cumulative operational cost across Phases 1-5.
    """
    __tablename__ = "llm_usage_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dispute_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    phase: Mapped[str] = mapped_column(String, nullable=False)          # e.g. "phase3", "phase4", "phase5"
    node: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # e.g. "case_strength", "reasoning"
    model: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    input_cost: Mapped[float] = mapped_column(Float, default=0.0)
    output_cost: Mapped[float] = mapped_column(Float, default=0.0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

# --- Phase 8.5: Chatbot Memory ---
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    merchant_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    session_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    role: Mapped[str] = mapped_column(String, nullable=False)  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
