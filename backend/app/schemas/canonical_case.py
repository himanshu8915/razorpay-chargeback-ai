from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class CustomerSchema(BaseModel):
    customer_id: str
    customer_city: str
    customer_state: str
    customer_zip_code_prefix: str
    customer_region: str
    customer_name: str
    customer_email: str
    customer_phone: str
    model_config = ConfigDict(from_attributes=True)

class MerchantSchema(BaseModel):
    merchant_id: str
    seller_city: str
    seller_state: str
    seller_zip_code_prefix: str
    merchant_region: str
    merchant_name: str
    merchant_email: str
    merchant_phone: str
    model_config = ConfigDict(from_attributes=True)

class OrderSchema(BaseModel):
    order_id: str
    order_status: str
    order_purchase_timestamp: Optional[datetime]
    order_approved_at: Optional[datetime]
    order_delivered_carrier_date: Optional[datetime]
    order_delivered_customer_date: Optional[datetime]
    order_estimated_delivery_date: Optional[datetime]
    delivery_delay_days: Optional[float]
    purchase_to_delivery_days: Optional[float]
    derived_delivery_state: str
    order_channel: str
    model_config = ConfigDict(from_attributes=True)

class TransactionSchema(BaseModel):
    transaction_id: str
    payment_type: str
    payment_installments: int
    payment_value: float
    payment_total: float
    payment_count: int
    transaction_status: str
    authorization_status: str
    model_config = ConfigDict(from_attributes=True)

class DeliverySchema(BaseModel):
    delivery_id: str
    order_id: str
    order_delivered_carrier_date: Optional[datetime]
    order_delivered_customer_date: Optional[datetime]
    order_estimated_delivery_date: Optional[datetime]
    delivery_delay_days: Optional[float]
    delivery_state: str
    tracking_id: str
    carrier_name: str
    model_config = ConfigDict(from_attributes=True)

class DisputeSchema(BaseModel):
    dispute_id: str
    transaction_id: str
    canonical_order_id: str
    dispute_type: str
    dispute_reason: str
    dispute_amount: float
    dispute_opened_at: datetime
    dispute_status: str
    claim: str
    model_config = ConfigDict(from_attributes=True)

class CanonicalCase(BaseModel):
    dispute: DisputeSchema
    transaction: TransactionSchema
    order: OrderSchema
    delivery: DeliverySchema
    customer: CustomerSchema
    merchant: Optional[MerchantSchema]
    
    # Operational deadline metadata
    deadline: datetime
    deadline_source: str
    response_window_days: int
