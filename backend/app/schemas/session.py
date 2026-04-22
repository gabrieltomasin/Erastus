import datetime

from pydantic import BaseModel


class SessionCreate(BaseModel):
    campaign_id: int
    title: str


class ReorderRequest(BaseModel):
    session_ids: list[int]


class SessionUpdate(BaseModel):
    title: str | None = None
    final_summary: str | None = None


class SessionOut(BaseModel):
    id: int
    campaign_id: int
    title: str
    session_number: int
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class SessionDetail(SessionOut):
    audio_files: list[dict] | None = None
    transcription: str | None = None
    raw_summary: str | None = None
    final_summary: str | None = None
    error_message: str | None = None
    processing_logs: list["ProcessingLogOut"] = []

    model_config = {"from_attributes": True}


from app.schemas.processing_log import ProcessingLogOut  # noqa: E402

SessionDetail.model_rebuild()
