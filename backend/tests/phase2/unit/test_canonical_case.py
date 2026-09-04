import pytest
from datetime import datetime
from pydantic import ValidationError
from app.schemas.canonical_case import CanonicalCase, DisputeSchema, TransactionSchema, OrderSchema, DeliverySchema

def test_canonical_case_validation():
    # Test valid construction
    dispute = DisputeSchema(
        dispute_id="DSP1", transaction_id="TX1", canonical_order_id="ORD1",
        dispute_type="fraud", dispute_reason="unauth", dispute_amount=100.0,
        dispute_opened_at=datetime.utcnow(), dispute_status="open", claim="claim"
    )
    transaction = TransactionSchema(
        transaction_id="TX1", payment_type="cc", payment_installments=1,
        payment_value=100.0, payment_total=100.0, payment_count=1,
        transaction_status="approved", authorization_status="auth"
    )
    order = OrderSchema(
        order_id="ORD1", order_status="delivered", derived_delivery_state="delivered",
        order_channel="web", order_purchase_timestamp=None, order_approved_at=None,
        order_delivered_carrier_date=None, order_delivered_customer_date=None,
        order_estimated_delivery_date=None, delivery_delay_days=None, purchase_to_delivery_days=None
    )
    delivery = DeliverySchema(
        delivery_id="DEL1", order_id="ORD1", delivery_state="delivered",
        tracking_id="TRK", carrier_name="FedEx", order_delivered_carrier_date=None,
        order_delivered_customer_date=None, order_estimated_delivery_date=None,
        delivery_delay_days=None
    )
    from app.schemas.canonical_case import CustomerSchema, MerchantSchema
    customer = CustomerSchema(
        customer_id="CUS1", customer_city="City", customer_state="ST",
        customer_zip_code_prefix="12345", customer_region="Region",
        customer_name="Name", customer_email="email@example.com",
        customer_phone="1234567890"
    )
    merchant = MerchantSchema(
        merchant_id="MER1", seller_city="City", seller_state="ST",
        seller_zip_code_prefix="12345", merchant_region="Region",
        merchant_name="Name", merchant_email="email@example.com",
        merchant_phone="1234567890"
    )
    
    case = CanonicalCase(
        dispute=dispute,
        transaction=transaction,
        order=order,
        delivery=delivery,
        customer=customer,
        merchant=merchant,
        deadline=datetime.utcnow(),
        deadline_source="test",
        response_window_days=30
    )
    
    assert case.dispute.dispute_id == "DSP1"
    
    # Missing required field
    with pytest.raises(ValidationError):
        CanonicalCase(
            transaction=transaction,
            order=order,
            delivery=delivery,
            deadline=datetime.utcnow(),
            deadline_source="test",
            response_window_days=30
        )

def test_canonical_case_optional_merchant():
    dispute = DisputeSchema(dispute_id="DSP1", transaction_id="TX1", canonical_order_id="ORD1", dispute_type="fraud", dispute_reason="unauth", dispute_amount=100.0, dispute_opened_at=datetime.utcnow(), dispute_status="open", claim="claim")
    transaction = TransactionSchema(transaction_id="TX1", payment_type="cc", payment_installments=1, payment_value=100.0, payment_total=100.0, payment_count=1, transaction_status="approved", authorization_status="auth")
    order = OrderSchema(order_id="ORD1", order_status="delivered", derived_delivery_state="delivered", order_channel="web", order_purchase_timestamp=None, order_approved_at=None, order_delivered_carrier_date=None, order_delivered_customer_date=None, order_estimated_delivery_date=None, delivery_delay_days=None, purchase_to_delivery_days=None)
    delivery = DeliverySchema(delivery_id="DEL1", order_id="ORD1", delivery_state="delivered", tracking_id="TRK", carrier_name="FedEx", order_delivered_carrier_date=None, order_delivered_customer_date=None, order_estimated_delivery_date=None, delivery_delay_days=None)
    from app.schemas.canonical_case import CustomerSchema
    customer = CustomerSchema(customer_id="CUS1", customer_city="City", customer_state="ST", customer_zip_code_prefix="12345", customer_region="Region", customer_name="Name", customer_email="email@example.com", customer_phone="1234567890")
    
    case = CanonicalCase(
        dispute=dispute,
        transaction=transaction,
        order=order,
        delivery=delivery,
        customer=customer,
        merchant=None,
        deadline=datetime.utcnow(),
        deadline_source="test",
        response_window_days=30
    )
    assert case.merchant is None
