from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Customer
from .base_repository import BaseRepository

class CustomerRepository(BaseRepository[Customer]):
    def __init__(self, session: AsyncSession):
        super().__init__(Customer, session)
