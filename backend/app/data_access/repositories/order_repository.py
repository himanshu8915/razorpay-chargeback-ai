from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Order
from .base_repository import BaseRepository

class OrderRepository(BaseRepository[Order]):
    def __init__(self, session: AsyncSession):
        super().__init__(Order, session)
