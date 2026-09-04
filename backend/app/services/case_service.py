from sqlalchemy.ext.asyncio import AsyncSession
from app.data_access.repositories.dispute_repository import DisputeRepository
from app.data_access.repositories.transaction_repository import TransactionRepository
from app.data_access.repositories.order_repository import OrderRepository
from app.data_access.repositories.customer_repository import CustomerRepository
from app.data_access.repositories.merchant_repository import MerchantRepository
from app.data_access.repositories.delivery_repository import DeliveryRepository
from app.schemas.canonical_case import CanonicalCase, DisputeSchema, TransactionSchema, OrderSchema, DeliverySchema, CustomerSchema, MerchantSchema
from app.services.deadline_resolver import resolve_deadline

class CaseAssemblyError(Exception):
    def __init__(self, message: str, missing_entity: str = None):
        super().__init__(message)
        self.missing_entity = missing_entity

class CaseService:
    def __init__(self, session: AsyncSession):
        self.dispute_repo = DisputeRepository(session)
        self.transaction_repo = TransactionRepository(session)
        self.order_repo = OrderRepository(session)
        self.customer_repo = CustomerRepository(session)
        self.merchant_repo = MerchantRepository(session)
        self.delivery_repo = DeliveryRepository(session)

    async def get_case(self, dispute_id: str) -> CanonicalCase:
        # 1. Fetch Dispute
        dispute = await self.dispute_repo.get_by_id(dispute_id)
        if not dispute:
            return None # None triggers 404

        # 2. Fetch Transaction
        transaction = await self.transaction_repo.get_by_id(dispute.transaction_id)
        if not transaction:
            raise CaseAssemblyError(f"Transaction {dispute.transaction_id} not found for dispute {dispute_id}", missing_entity="transaction")

        # 3. Fetch Order
        order = await self.order_repo.get_by_id(dispute.canonical_order_id)
        if not order:
            raise CaseAssemblyError(f"Order {dispute.canonical_order_id} not found for dispute {dispute_id}", missing_entity="order")

        if getattr(transaction, 'order_id', None) != dispute.canonical_order_id:
            raise CaseAssemblyError(f"Transaction order_id mismatch", missing_entity="transaction_link")

        # 4. Fetch Delivery (Optional)
        delivery = await self.delivery_repo.get_by_order_id(order.order_id)
        if not delivery:
            raise CaseAssemblyError(f"Delivery not found for order {order.order_id}", missing_entity="delivery")

        # 5. Fetch Customer and Merchant
        customer = await self.customer_repo.get_by_id(getattr(order, 'customer_id', None))
        if not customer:
            raise CaseAssemblyError(f"Customer not found for order {order.order_id}", missing_entity="customer")

        merchant_id = getattr(order, 'merchant_id', None)
        merchant = None
        if merchant_id is not None:
            merchant = await self.merchant_repo.get_by_id(merchant_id)
            if not merchant:
                raise CaseAssemblyError(f"Merchant {merchant_id} not found for order {order.order_id}", missing_entity="merchant")

        # 6. Resolve Deadline
        deadline, source, window = resolve_deadline(dispute.dispute_opened_at)

        return CanonicalCase(
            dispute=DisputeSchema.model_validate(dispute),
            transaction=TransactionSchema.model_validate(transaction),
            order=OrderSchema.model_validate(order),
            delivery=DeliverySchema.model_validate(delivery),
            customer=CustomerSchema.model_validate(customer),
            merchant=MerchantSchema.model_validate(merchant) if merchant else None,
            deadline=deadline,
            deadline_source=source,
            response_window_days=window
        )
