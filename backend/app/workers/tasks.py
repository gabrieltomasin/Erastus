import logging

from app.workers.celery_app import celery_app
from app.workers.transcribe import transcribe_session
from app.workers.summarize import summarize_session

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def process_session(self, session_id: int):
    """Main pipeline: transcribe then summarize."""
    chain = transcribe_session.s(session_id) | _dispatch_summarize.s()
    chain.apply_async()


@celery_app.task
def _dispatch_summarize(result):
    """Ignore transcription result and dispatch summarization with the original session_id."""
    if isinstance(result, dict) and "session_id" in result:
        session_id = result["session_id"]
    else:
        logger.error(f"Unexpected transcription result: {result}")
        return
    summarize_session.delay(session_id)
