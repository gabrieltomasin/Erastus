import asyncio
import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=1)
def summarize_session(self, session_id: int) -> dict:
    """Summarize a transcribed session using LLM."""
    from sqlalchemy import select
    from app.database import worker_session
    from app.models.session import Session, SessionStatus
    from app.models.processing_log import ProcessingLog
    from app.services.summarizer import LLMClient

    async def _run():
        async with worker_session() as db:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                return {"error": "Session not found"}

            if not session.transcription:
                session.status = SessionStatus.ERROR
                session.error_message = "No transcription available for summarization"
                await db.commit()
                return {"error": "No transcription"}

            try:
                session.status = SessionStatus.SUMMARIZING
                log = ProcessingLog(
                    session_id=session_id,
                    step="summarization",
                    message="Iniciando geração de resumo...",
                )
                db.add(log)
                await db.commit()

                # Load campaign for context
                from app.models.campaign import Campaign
                camp_result = await db.execute(
                    select(Campaign).where(Campaign.id == session.campaign_id)
                )
                campaign = camp_result.scalar_one_or_none()

                context = campaign.general_context if campaign else None
                custom_prompt = campaign.system_prompt if campaign else None

                # Summarize
                client = LLMClient()
                summary = client.summarize(
                    transcription=session.transcription,
                    context=context,
                    custom_prompt=custom_prompt,
                )

                session.raw_summary = summary
                session.final_summary = summary
                session.status = SessionStatus.READY

                log2 = ProcessingLog(
                    session_id=session_id,
                    step="summarization",
                    message=f"Resumo gerado: {len(summary)} caracteres",
                )
                db.add(log2)
                await db.commit()

                return {"session_id": session_id, "status": "ready"}

            except Exception as e:
                session.status = SessionStatus.ERROR
                session.error_message = str(e)
                log = ProcessingLog(
                    session_id=session_id,
                    step="summarization",
                    message=f"Erro: {e}",
                    level="error",
                )
                db.add(log)
                await db.commit()
                raise

    return asyncio.run(_run())
