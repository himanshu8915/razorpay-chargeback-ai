import pytest
from unittest.mock import AsyncMock
from datetime import datetime
from app.services.case_service import CaseService, CaseAssemblyError
from app.db.models import Dispute, Transaction, Order, Delivery, Customer, Merchant

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_case_service_success(mock_session):
    service = CaseService(mock_session)
    
    # Mock repos
    service.dispute_repo.get_by_id = AsyncMock(return_value=Dispute(
        dispute_id="DSP1", 
        transaction_id="TX1", 
        canonical_order_id="ORD1",
        dispute_type="fraud",
        dispute_reason="unauthorized",
        dispute_amount=100.0,
        dispute_opened_at=datetime.utcnow(),
        dispute_status="open",
        claim="Fraud claim"
    ))
    
    service.transaction_repo.get_by_id = AsyncMock(return_value=Transaction(
        transaction_id="TX1",
        order_id="ORD1",
        payment_type="credit_card",
        payment_installments=1,
        payment_value=100.0,
        payment_total=100.0,
        payment_count=1,
        transaction_status="approved",
        authorization_status="authorized"
    ))

    service.order_repo.get_by_id = AsyncMock(return_value=Order(
        order_id="ORD1",
        customer_id="CUS1",
        merchant_id="MER1",
        order_status="delivered",
        derived_delivery_state="delivered",
        order_channel="web"
    ))

    service.customer_repo.get_by_id = AsyncMock(return_value=Customer(
        customer_id="CUS1", customer_city="City", customer_state="ST",
        customer_zip_code_prefix="12345", customer_region="Region",
        customer_name="Name", customer_email="email@example.com",
        customer_phone="1234567890"
    ))

    service.merchant_repo.get_by_id = AsyncMock(return_value=Merchant(
        merchant_id="MER1", seller_city="City", seller_state="ST",
        seller_zip_code_prefix="12345", merchant_region="Region",
        merchant_name="Name", merchant_email="email@example.com",
        merchant_phone="1234567890"
    ))

    service.delivery_repo.get_by_order_id = AsyncMock(return_value=Delivery(
        delivery_id="DEL1",
        order_id="ORD1",
        delivery_state="delivered",
        tracking_id="TRK1",
        carrier_name="FedEx"
    ))
    
    case = await service.get_case("DSP1")
    assert case is not None
    assert case.dispute.dispute_id == "DSP1"
    assert case.transaction.transaction_id == "TX1"
    assert case.order.order_id == "ORD1"
    assert case.customer.customer_id == "CUS1"
    assert case.merchant.merchant_id == "MER1"

@pytest.mark.asyncio
async def test_case_service_missing_transaction(mock_session):
    service = CaseService(mock_session)
    service.dispute_repo.get_by_id = AsyncMock(return_value=Dispute(
        dispute_id="DSP1", transaction_id="TX1", canonical_order_id="ORD1"
    ))
    # Transaction returns None
    service.transaction_repo.get_by_id = AsyncMock(return_value=None)
    
    with pytest.raises(CaseAssemblyError) as exc:
        await service.get_case("DSP1")
    assert exc.value.missing_entity == "transaction"

@pytest.mark.asyncio
async def test_case_service_merchant_null(mock_session):
    service = CaseService(mock_session)
    service.dispute_repo.get_by_id = AsyncMock(return_value=Dispute(
        dispute_id="DSP1", transaction_id="TX1", canonical_order_id="ORD1",
        dispute_opened_at=datetime.utcnow(), dispute_status="open", claim="claim", dispute_type="fraud", dispute_reason="reason", dispute_amount=100.0
    ))
    service.transaction_repo.get_by_id = AsyncMock(return_value=Transaction(
        transaction_id="TX1", order_id="ORD1", payment_type="cc", payment_installments=1, payment_value=100.0, payment_total=100.0, payment_count=1, transaction_status="approved", authorization_status="auth"
    ))
    # Note: merchant_id is None
    service.order_repo.get_by_id = AsyncMock(return_value=Order(
        order_id="ORD1", customer_id="CUS1", merchant_id=None, order_status="delivered", derived_delivery_state="delivered", order_channel="web"
    ))
    service.customer_repo.get_by_id = AsyncMock(return_value=Customer(
        customer_id="CUS1", customer_city="City", customer_state="ST", customer_zip_code_prefix="12345", customer_region="Region", customer_name="Name", customer_email="email", customer_phone="phone"
    ))
    service.delivery_repo.get_by_order_id = AsyncMock(return_value=Delivery(
        delivery_id="DEL1", order_id="ORD1", delivery_state="delivered", tracking_id="TRK1", carrier_name="FedEx"
    ))
    
    case = await service.get_case("DSP1")
    assert case is not None
    assert case.merchant is None

@pytest.mark.asyncio
async def test_case_service_merchant_missing(mock_session):
    service = CaseService(mock_session)
    service.dispute_repo.get_by_id = AsyncMock(return_value=Dispute(
        dispute_id="DSP1", transaction_id="TX1", canonical_order_id="ORD1",
        dispute_opened_at=datetime.utcnow()
    ))
    service.transaction_repo.get_by_id = AsyncMock(return_value=Transaction(
        transaction_id="TX1", order_id="ORD1"
    ))
    # Note: merchant_id is present
    service.order_repo.get_by_id = AsyncMock(return_value=Order(
        order_id="ORD1", customer_id="CUS1", merchant_id="MER1"
    ))
    service.customer_repo.get_by_id = AsyncMock(return_value=Customer(
        customer_id="CUS1", customer_city="City", customer_state="ST", customer_zip_code_prefix="12345", customer_region="Region", customer_name="Name", customer_email="email", customer_phone="phone"
    ))
    service.delivery_repo.get_by_order_id = AsyncMock(return_value=Delivery(
        delivery_id="DEL1", order_id="ORD1"
    ))
    # But repo returns None
    service.merchant_repo.get_by_id = AsyncMock(return_value=None)
    
    with pytest.raises(CaseAssemblyError) as exc:
        await service.get_case("DSP1")
    assert exc.value.missing_entity == "merchant"
