from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Merchant
from .base_repository import BaseRepository

class MerchantRepository(BaseRepository[Merchant]):
    def __init__(self, session: AsyncSession):
        super().__init__(Merchant, session)
