from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings


engine = create_async_engine(settings.database_url)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass

# get_db is a dependency function that provides sessions to our routes
# fastapi's dependency injection calls this function for every request
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session