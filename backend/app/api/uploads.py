import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.session import Session, SessionStatus
from app.models.processing_log import ProcessingLog
from app.schemas.session import SessionDetail
from app.services.storage import storage
from app.services.zip_handler import extract_audio_from_zip, AUDIO_EXTENSIONS

router = APIRouter()

MAX_FILE_SIZE = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024


@router.post("/{session_id}/upload", response_model=SessionDetail)
async def upload_audio(
    session_id: int,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    if session.status not in (SessionStatus.PENDING, SessionStatus.ERROR, SessionStatus.READY):
        raise HTTPException(400, f"Cannot upload to session in status: {session.status.value}")

    # Copy before appending: mutating the loaded JSON list in place poisons
    # SQLAlchemy's change detection (the committed state references the same
    # object), which silently drops appended files on later uploads
    audio_files = list(session.audio_files or [])
    session_dir = storage.get_session_dir(session_id)

    for upload in files:
        filename = upload.filename or "unknown"
        ext = Path(filename).suffix.lower()

        # Check if it's a ZIP
        if ext == ".zip":
            # Save ZIP temporarily
            zip_path = session_dir / filename
            content = await upload.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(400, f"ZIP file too large (max {settings.MAX_AUDIO_SIZE_MB}MB)")
            zip_path.write_bytes(content)

            # Extract audio files
            extracted = extract_audio_from_zip(str(zip_path), str(session_dir))
            zip_path.unlink()  # Remove ZIP after extraction

            if not extracted:
                raise HTTPException(400, "No audio files found in ZIP archive")

            for extracted_path in extracted:
                f = Path(extracted_path)
                audio_files.append({
                    "filename": f.name,
                    "size": f.stat().st_size,
                    "path": str(f),
                })

            # Log extraction
            log = ProcessingLog(
                session_id=session_id,
                step="upload",
                message=f"Extraídos {len(extracted)} arquivos de áudio do ZIP",
            )
            db.add(log)

        elif ext in AUDIO_EXTENSIONS:
            content = await upload.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(400, f"File too large (max {settings.MAX_AUDIO_SIZE_MB}MB)")

            filepath = storage.save(session_id, filename, content)
            audio_files.append({
                "filename": filename,
                "size": len(content),
                "path": filepath,
            })

            log = ProcessingLog(
                session_id=session_id,
                step="upload",
                message=f"Upload recebido: {filename} ({len(content) / 1024 / 1024:.1f}MB)",
            )
            db.add(log)
        else:
            raise HTTPException(400, f"Unsupported file type: {ext}. Accepted: {', '.join(AUDIO_EXTENSIONS)}, .zip")

    # audio_files is a fresh copy, so this assignment registers as a change
    session.audio_files = audio_files

    # Clear previous results when replacing files
    session.transcription = None
    session.raw_summary = None
    session.final_summary = None
    session.error_message = None
    session.status = SessionStatus.PENDING

    # Update status and dispatch processing task
    if audio_files:
        session.status = SessionStatus.PENDING
        log = ProcessingLog(
            session_id=session_id,
            step="upload",
            message=f"Upload completo: {len(audio_files)} arquivo(s). Iniciando processamento...",
        )
        db.add(log)
        await db.commit()
        await db.refresh(session)

        # Dispatch Celery task
        from app.workers.tasks import process_session
        process_session.delay(session_id)

    await db.commit()
    await db.refresh(session)

    # Return full session detail
    from app.api.sessions import get_session
    return await get_session(session_id, db)
