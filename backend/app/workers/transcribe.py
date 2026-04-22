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

                all_segments = []  # list of {start, end, text, file}
                file_durations = []  # track duration per file

                for i, af in enumerate(audio_files):
                    file_path = af.get("path", "")
                    if not Path(file_path).exists():
                        raise FileNotFoundError(f"Audio file not found: {file_path}")

                    filename = af.get("filename", f"Arquivo {i+1}")
                    msg = f"Transcrevendo arquivo {i + 1}/{len(audio_files)}: {filename}"
                    await _log(db, session_id, "transcription", msg)
                    await db.commit()

                    publish_log(session_id, "transcription", msg)
                    publish_progress(session_id, "transcription", i + 1, len(audio_files), filename)

                    trans_result = transcriber.transcribe(file_path)

                    # Collect segments — timestamps are relative to each file's start
                    # When multiple files are simultaneous recordings from different sources,
                    # interleaving by timestamp reconstructs the real dialogue order
                    for seg in trans_result.segments:
                        all_segments.append({
                            "start": seg["start"],
                            "end": seg["end"],
                            "text": seg["text"],
                            "file": filename,
                        })

                    file_durations.append(trans_result.duration)
                    af["duration"] = round(trans_result.duration, 1)

                # Interleave segments by time across all files
                all_segments.sort(key=lambda s: s["start"])

                # Build speaker map (file index -> speaker_N)
                speaker_map = {}
                for i, af in enumerate(audio_files):
                    speaker_map[af.get("filename", f"Arquivo {i+1}")] = f"speaker_{i+1}"

                # Build interleaved transcription
                if len(audio_files) > 1 and len(all_segments) > 0:
                    lines = []
                    current_speaker = None
                    for seg in all_segments:
                        speaker = speaker_map.get(seg["file"], "speaker_?")
                        timestamp = f"[{_format_time(seg['start'])}]"
                        if speaker != current_speaker:
                            lines.append(f"\n**{speaker}:** {timestamp} {seg['text']}")
                            current_speaker = speaker
                        else:
                            lines.append(f"{timestamp} {seg['text']}")
                    full_transcription = "\n".join(lines).strip()
                elif len(all_segments) > 0:
                    # Single file — simple transcription
                    lines = []
                    for seg in all_segments:
                        lines.append(seg["text"])
                    full_transcription = " ".join(lines)
                else:
                    full_transcription = trans_result.text
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


def _format_time(seconds: float) -> str:
    """Format seconds to HH:MM:SS or MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


async def _log(db, session_id: int, step: str, message: str, level: str = "info"):
    from app.models.processing_log import ProcessingLog
    log = ProcessingLog(session_id=session_id, step=step, message=message, level=level)
    db.add(log)
