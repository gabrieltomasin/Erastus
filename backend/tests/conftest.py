import asyncio
from collections.abc import AsyncGenerator, Callable

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://rpg:rpg@[::1]:5432/rpgsummary_test"

# NullPool: asyncpg connections are event-loop-bound, and pytest-asyncio
# creates a fresh loop per test — pooled connections from a previous
# test's loop would fail.
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def celery_calls(monkeypatch) -> dict:
    """Stub .delay on worker tasks so endpoints can dispatch without a broker.

    Returns a dict of task name -> list of call args.
    """
    from app.workers.summarize import summarize_session
    from app.workers.tasks import _dispatch_summarize, process_session

    calls: dict[str, list] = {"process_session": [], "summarize_session": [], "_dispatch_summarize": []}
    monkeypatch.setattr(
        process_session, "delay", lambda *a, **k: calls["process_session"].append(a)
    )
    monkeypatch.setattr(
        summarize_session, "delay", lambda *a, **k: calls["summarize_session"].append(a)
    )
    monkeypatch.setattr(
        _dispatch_summarize,
        "delay",
        lambda *a, **k: calls["_dispatch_summarize"].append(a),
    )
    return calls


@pytest.fixture
def make_campaign(client) -> Callable:
    async def _make(**overrides) -> dict:
        payload = {"title": "Campanha Teste", **overrides}
        resp = await client.post("/api/campaigns", json=payload)
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make


@pytest.fixture
def make_session(client, make_campaign) -> Callable:
    async def _make(campaign_id: int | None = None, title: str = "Sessão Teste") -> dict:
        if campaign_id is None:
            campaign_id = (await make_campaign())["id"]
        resp = await client.post(
            "/api/sessions", json={"campaign_id": campaign_id, "title": title}
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make


@pytest.fixture
def set_session_status():
    """Bypass the API to place a session in an arbitrary pipeline state."""

    async def _set(session_id: int, status: str, **fields):
        from sqlalchemy import select

        from app.models.session import Session, SessionStatus

        async with test_session_factory() as db:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one()
            session.status = SessionStatus(status)
            for key, value in fields.items():
                setattr(session, key, value)
            await db.commit()

    return _set
