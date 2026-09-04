from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Transaction
from .base_repository import BaseRepository

class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, session: AsyncSession):
        super().__init__(Transaction, session)
