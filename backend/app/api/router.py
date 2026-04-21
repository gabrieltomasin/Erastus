from fastapi import APIRouter

from app.api.campaigns import router as campaigns_router
from app.api.sessions import router as sessions_router
from app.api.uploads import router as uploads_router
from app.api.ws import router as ws_router

api_router = APIRouter()
api_router.include_router(campaigns_router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(sessions_router, prefix="/sessions", tags=["sessions"])
api_router.include_router(uploads_router, prefix="/sessions", tags=["uploads"])
api_router.include_router(ws_router)


@api_router.get("/health")
async def health_check():
    return {"status": "ok"}
