from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from app.db.models import Delivery
from .base_repository import BaseRepository

class DeliveryRepository(BaseRepository[Delivery]):
    def __init__(self, session: AsyncSession):
        super().__init__(Delivery, session)

    async def get_by_order_id(self, order_id: str) -> Optional[Delivery]:
        result = await self.session.execute(select(Delivery).filter(Delivery.order_id == order_id))
        return result.scalars().first()
