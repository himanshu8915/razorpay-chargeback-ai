-- =============================================================
-- Razorpay Chargeback AI — Application Schema
-- PostgreSQL 16 + pgvector
-- =============================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- System metadata
CREATE TABLE IF NOT EXISTS system_metadata (
    key VARCHAR PRIMARY KEY,
    value VARCHAR NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Customers
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR PRIMARY KEY,
    customer_city VARCHAR,
    customer_state VARCHAR,
    customer_zip_code_prefix VARCHAR,
    customer_region VARCHAR,
    customer_name VARCHAR,
    customer_email VARCHAR,
    customer_phone VARCHAR
);

-- Merchants
CREATE TABLE IF NOT EXISTS merchants (
    merchant_id VARCHAR PRIMARY KEY,
    seller_city VARCHAR,
    seller_state VARCHAR,
    seller_zip_code_prefix VARCHAR,
    merchant_region VARCHAR,
    merchant_name VARCHAR,
    merchant_email VARCHAR,
    merchant_phone VARCHAR
);

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR PRIMARY KEY,
    customer_id VARCHAR REFERENCES customers(customer_id),
    merchant_id VARCHAR REFERENCES merchants(merchant_id),
    order_status VARCHAR,
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,
    delivery_delay_days FLOAT,
    purchase_to_delivery_days FLOAT,
    derived_delivery_state VARCHAR,
    order_channel VARCHAR
);

-- Transactions
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR PRIMARY KEY,
    order_id VARCHAR REFERENCES orders(order_id),
    payment_type VARCHAR,
    payment_installments INTEGER,
    payment_value FLOAT,
    payment_total FLOAT,
    payment_count INTEGER,
    transaction_status VARCHAR,
    authorization_status VARCHAR
);

-- Deliveries
CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id VARCHAR PRIMARY KEY,
    order_id VARCHAR REFERENCES orders(order_id),
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,
    delivery_delay_days FLOAT,
    delivery_state VARCHAR,
    tracking_id VARCHAR,
    carrier_name VARCHAR
);

-- Disputes
CREATE TABLE IF NOT EXISTS disputes (
    dispute_id VARCHAR PRIMARY KEY,
    transaction_id VARCHAR REFERENCES transactions(transaction_id),
    canonical_order_id VARCHAR REFERENCES orders(order_id),
    dispute_type VARCHAR,
    dispute_reason VARCHAR,
    dispute_amount FLOAT,
    dispute_opened_at TIMESTAMP,
    dispute_status VARCHAR,
    claim TEXT
);

-- Policy documents
CREATE TABLE IF NOT EXISTS policy_documents (
    policy_id VARCHAR PRIMARY KEY,
    title VARCHAR,
    source_file VARCHAR,
    version VARCHAR
);

-- Policy parent chunks
CREATE TABLE IF NOT EXISTS policy_parent_chunks (
    parent_chunk_id VARCHAR PRIMARY KEY,
    policy_id VARCHAR REFERENCES policy_documents(policy_id),
    content TEXT,
    page INTEGER
);

-- Policy child chunks with pgvector embeddings (768-dim Gemini)
CREATE TABLE IF NOT EXISTS policy_child_chunks (
    child_chunk_id VARCHAR PRIMARY KEY,
    parent_chunk_id VARCHAR NOT NULL REFERENCES policy_parent_chunks(parent_chunk_id),
    policy_id VARCHAR NOT NULL REFERENCES policy_documents(policy_id),
    content TEXT NOT NULL,
    embedding vector(768)
);

-- Decision artifacts (runtime mutable — written by Phase 5)
CREATE TABLE IF NOT EXISTS decision_artifacts (
    decision_artifact_id VARCHAR PRIMARY KEY,
    dispute_id VARCHAR REFERENCES disputes(dispute_id),
    decision VARCHAR,
    confidence FLOAT,
    case_strength FLOAT,
    success_likelihood FLOAT,
    recoverable_amount FLOAT,
    expected_recovery FLOAT,
    estimated_operational_cost FLOAT,
    net_expected_value FLOAT,
    token_usage JSON,
    token_cost JSON,
    reason_codes JSON,
    key_evidence JSON,
    supporting_evidence JSON,
    contradicting_evidence JSON,
    missing_evidence JSON,
    risk_flags JSON,
    deadline VARCHAR,
    deadline_risk VARCHAR,
    next_action VARCHAR,
    rationale VARCHAR,
    workflow_status VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Human reviews (runtime mutable — written by HITL actions)
CREATE TABLE IF NOT EXISTS human_reviews (
    review_id VARCHAR PRIMARY KEY,
    decision_artifact_id VARCHAR REFERENCES decision_artifacts(decision_artifact_id),
    dispute_id VARCHAR REFERENCES disputes(dispute_id),
    ai_recommendation JSON,
    ai_confidence FLOAT,
    ai_explanation JSON,
    human_action VARCHAR,
    human_reason VARCHAR,
    edited_decision VARCHAR,
    edited_response VARCHAR,
    reviewer_id VARCHAR,
    review_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    previous_state VARCHAR,
    new_state VARCHAR
);

-- LLM usage records (runtime mutable — written per LLM call)
CREATE TABLE IF NOT EXISTS llm_usage_records (
    id SERIAL PRIMARY KEY,
    dispute_id VARCHAR NOT NULL,
    phase VARCHAR NOT NULL,
    node VARCHAR,
    model VARCHAR,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    input_cost FLOAT DEFAULT 0.0,
    output_cost FLOAT DEFAULT 0.0,
    total_cost FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_llm_usage_records_dispute_id ON llm_usage_records(dispute_id);

-- Chat messages (chatbot memory)
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    merchant_id VARCHAR NOT NULL,
    session_id VARCHAR,
    role VARCHAR NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_chat_messages_merchant_id ON chat_messages(merchant_id);
CREATE INDEX IF NOT EXISTS ix_chat_messages_session_id ON chat_messages(session_id);

-- pgvector IVFFlat index for fast cosine similarity search on policy embeddings
CREATE INDEX IF NOT EXISTS ix_policy_child_chunks_embedding
    ON policy_child_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 20);

SELECT 'Schema created successfully.' AS status;
