from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import TypeVar, Generic, Type, Optional
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id_value: str) -> Optional[ModelType]:
        result = await self.session.execute(select(self.model).filter(self.model.__mapper__.primary_key[0] == id_value))
        return result.scalars().first()
