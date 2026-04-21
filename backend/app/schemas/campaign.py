import datetime

from pydantic import BaseModel


class CampaignCreate(BaseModel):
    title: str
    description: str = ""
    system_prompt: str | None = None


class CampaignUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    general_context: str | None = None


class CampaignOut(BaseModel):
    id: int
    title: str
    description: str
    session_count: int = 0
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class CampaignDetail(CampaignOut):
    general_context: str | None = None
    system_prompt: str | None = None
    context_updated_at: datetime.datetime | None = None
    sessions: list["SessionBrief"] = []

    model_config = {"from_attributes": True}


class SessionBrief(BaseModel):
    id: int
    title: str
    session_number: int
    status: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
