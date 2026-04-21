import datetime

from pydantic import BaseModel


class ProcessingLogOut(BaseModel):
    id: int
    session_id: int
    step: str
    message: str
    level: str
    timestamp: datetime.datetime

    model_config = {"from_attributes": True}
