from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.campaign import Campaign
from app.models.session import Session
from app.schemas.campaign import (
    CampaignCreate,
    CampaignDetail,
    CampaignOut,
    CampaignUpdate,
    SessionBrief,
)

router = APIRouter()


@router.get("", response_model=list[CampaignOut])
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    stmt = select(Campaign).order_by(Campaign.updated_at.desc())
    result = await db.execute(stmt)
    campaigns = result.scalars().all()

    out = []
    for c in campaigns:
        count_stmt = select(func.count()).where(Session.campaign_id == c.id)
        count_result = await db.execute(count_stmt)
        session_count = count_result.scalar() or 0
        out.append(CampaignOut(session_count=session_count, **c.__dict__))
    return out


@router.post("", response_model=CampaignOut, status_code=201)
async def create_campaign(data: CampaignCreate, db: AsyncSession = Depends(get_db)):
    campaign = Campaign(**data.model_dump())
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return CampaignOut(session_count=0, **campaign.__dict__)


@router.get("/{campaign_id}", response_model=CampaignDetail)
async def get_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Campaign)
        .options(selectinload(Campaign.sessions))
        .where(Campaign.id == campaign_id)
    )
    result = await db.execute(stmt)
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    sessions = [
        SessionBrief(
            id=s.id,
            title=s.title,
            session_number=s.session_number,
            status=s.status.value,
            created_at=s.created_at,
        )
        for s in campaign.sessions
    ]
    return CampaignDetail(
        session_count=len(sessions),
        sessions=sessions,
        **{k: v for k, v in campaign.__dict__.items() if k != "sessions"},
    )


@router.put("/{campaign_id}", response_model=CampaignDetail)
async def update_campaign(
    campaign_id: int, data: CampaignUpdate, db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Campaign)
        .options(selectinload(Campaign.sessions))
        .where(Campaign.id == campaign_id)
    )
    result = await db.execute(stmt)
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(campaign, key, value)

    await db.commit()
    await db.refresh(campaign)

    sessions = [
        SessionBrief(
            id=s.id,
            title=s.title,
            session_number=s.session_number,
            status=s.status.value,
            created_at=s.created_at,
        )
        for s in campaign.sessions
    ]
    return CampaignDetail(
        session_count=len(sessions),
        sessions=sessions,
        **{k: v for k, v in campaign.__dict__.items() if k != "sessions"},
    )


@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    await db.delete(campaign)
    await db.commit()


@router.post("/{campaign_id}/regenerate-context", response_model=CampaignDetail)
async def regenerate_context(campaign_id: int, db: AsyncSession = Depends(get_db)):
    from app.services.context import update_campaign_context

    try:
        await update_campaign_context(db, campaign_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to generate context: {e}")

    return await get_campaign(campaign_id, db)
