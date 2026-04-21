import logging
from pathlib import Path

from app.services.transcriber import Transcriber
from app.workers.celery_app import celery_app
from app.workers.events import publish_status, publish_log, publish_progress

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=1)
def transcribe_session(self, session_id: int) -> dict:
    """Transcribe all audio files for a session."""
    import asyncio
    from sqlalchemy import select
    from app.database import worker_session
    from app.models.session import Session, SessionStatus
    from app.models.processing_log import ProcessingLog

    async def _run():
        async with worker_session() as db:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                return {"error": "Session not found"}

            try:
                session.status = SessionStatus.TRANSCRIBING
                await _log(db, session_id, "transcription", "Iniciando transcrição...")
                await db.commit()

                publish_status(session_id, "transcribing")
                publish_log(session_id, "transcription", "Iniciando transcrição...")

                transcriber = Transcriber()
                audio_files = session.audio_files or []

                if not audio_files:
                    raise ValueError("No audio files found for session")

                all_transcriptions = []
                for i, af in enumerate(audio_files):
                    file_path = af.get("path", "")
                    if not Path(file_path).exists():
                        raise FileNotFoundError(f"Audio file not found: {file_path}")

                    msg = f"Transcrevendo arquivo {i + 1}/{len(audio_files)}: {af.get('filename', 'unknown')}"
                    await _log(db, session_id, "transcription", msg)
                    await db.commit()

                    publish_log(session_id, "transcription", msg)
                    publish_progress(session_id, "transcription", i + 1, len(audio_files), af.get("filename", ""))

                    trans_result = transcriber.transcribe(file_path)

                    header = f"--- {af.get('filename', f'Arquivo {i+1}')} ---"
                    all_transcriptions.append(f"{header}\n{trans_result.text}")

                    af["duration"] = round(trans_result.duration, 1)

                full_transcription = "\n\n".join(all_transcriptions)
                session.transcription = full_transcription
                session.audio_files = audio_files

                msg = f"Transcrição completa: {len(full_transcription)} caracteres"
                await _log(db, session_id, "transcription", msg)
                await db.commit()

                publish_log(session_id, "transcription", msg)
                publish_status(session_id, "summarizing")

                return {"session_id": session_id, "status": "transcribed"}

            except Exception as e:
                session.status = SessionStatus.ERROR
                session.error_message = str(e)
                await _log(db, session_id, "transcription", f"Erro: {e}", level="error")
                await db.commit()

                publish_status(session_id, "error")
                publish_log(session_id, "transcription", f"Erro: {e}", level="error")
                raise

    return asyncio.run(_run())


async def _log(db, session_id: int, step: str, message: str, level: str = "info"):
    from app.models.processing_log import ProcessingLog
    log = ProcessingLog(session_id=session_id, step=step, message=message, level=level)
    db.add(log)
