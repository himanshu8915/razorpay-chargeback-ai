from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Dispute
from .base_repository import BaseRepository

class DisputeRepository(BaseRepository[Dispute]):
    def __init__(self, session: AsyncSession):
        super().__init__(Dispute, session)
