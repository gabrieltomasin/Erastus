from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.session import Session, SessionStatus
from app.schemas.processing_log import ProcessingLogOut
from app.schemas.session import SessionCreate, SessionDetail, SessionOut, SessionUpdate

router = APIRouter()


@router.get("", response_model=list[SessionOut])
async def list_sessions(campaign_id: int | None = None, db: AsyncSession = Depends(get_db)):
    stmt = select(Session).order_by(Session.position, Session.session_number)
    if campaign_id is not None:
        stmt = stmt.where(Session.campaign_id == campaign_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=SessionOut, status_code=201)
async def create_session(data: SessionCreate, db: AsyncSession = Depends(get_db)):
    # Auto-increment session_number within campaign
    max_stmt = select(func.max(Session.session_number)).where(
        Session.campaign_id == data.campaign_id
    )
    result = await db.execute(max_stmt)
    max_num = result.scalar() or 0

    # Auto-increment position within campaign
    max_pos_stmt = select(func.max(Session.position)).where(
        Session.campaign_id == data.campaign_id
    )
    pos_result = await db.execute(max_pos_stmt)
    max_pos = pos_result.scalar() or 0

    session = Session(
        campaign_id=data.campaign_id,
        title=data.title,
        session_number=max_num + 1,
        position=max_pos + 1,
        status=SessionStatus.PENDING,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(session_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Session)
        .options(selectinload(Session.processing_logs))
        .where(Session.id == session_id)
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    return SessionDetail(
        processing_logs=[
            ProcessingLogOut(
                id=log.id,
                session_id=log.session_id,
                step=log.step,
                message=log.message,
                level=log.level,
                timestamp=log.timestamp,
            )
            for log in session.processing_logs
        ],
        status=session.status.value,
        **{k: v for k, v in session.__dict__.items() if k != "processing_logs" and k != "status"},
    )


@router.put("/{session_id}", response_model=SessionDetail)
async def update_session(
    session_id: int, data: SessionUpdate, db: AsyncSession = Depends(get_db)
):
    stmt = select(Session).where(Session.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(session, key, value)

    await db.commit()
    await db.refresh(session)
    return await get_session(session_id, db)


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Session).where(Session.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    await db.delete(session)
    await db.commit()


@router.post("/{session_id}/retry", response_model=SessionDetail)
async def retry_session(session_id: int, db: AsyncSession = Depends(get_db)):
    """Retry processing a session from the failed step."""
    stmt = select(Session).where(Session.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    if session.status != SessionStatus.ERROR:
        raise HTTPException(400, "Can only retry sessions in error state")

    session.error_message = None

    if session.transcription:
        # Transcription done, only retry summarization
        session.status = SessionStatus.SUMMARIZING
        await db.commit()
        from app.workers.summarize import summarize_session
        summarize_session.delay(session_id)
    else:
        # Retry from transcription
        session.status = SessionStatus.PENDING
        await db.commit()
        from app.workers.tasks import process_session
        process_session.delay(session_id)

    return await get_session(session_id, db)
