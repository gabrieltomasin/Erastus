from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        yield session


def worker_session():
    """Create a fresh async session factory for Celery workers.

    Each asyncio.run() call creates a new event loop, so the module-level
    async_session can't be reused (asyncpg connections are loop-bound).
    """
    eng = create_async_engine(settings.DATABASE_URL, echo=False)
    factory = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)

    class _WorkerSession:
        def __init__(self, factory, eng):
            self._factory = factory
            self._eng = eng

        async def __aenter__(self):
            self._session = self._factory()
            return await self._session.__aenter__()

        async def __aexit__(self, *args):
            await self._session.__aexit__(*args)
            await self._eng.dispose()

    return _WorkerSession(factory, eng)
