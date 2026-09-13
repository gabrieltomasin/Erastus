import io
import zipfile

import pytest

from app.services.storage import LocalStorage


pytestmark = pytest.mark.asyncio


@pytest.fixture
def upload_storage(tmp_path, monkeypatch):
    """Point the upload endpoint's storage at a temp dir for this test."""
    storage = LocalStorage(str(tmp_path / "uploads"))
    monkeypatch.setattr("app.api.uploads.storage", storage)
    return storage


def _file(name: str, content: bytes, mime: str = "application/octet-stream"):
    return {"files": (name, content, mime)}


async def test_upload_to_missing_session(client):
    resp = await client.post(
        "/api/sessions/9999/upload", files=_file("a.mp3", b"audio")
    )
    assert resp.status_code == 404


async def test_upload_rejects_unsupported_extension(client, make_session):
    session = await make_session()
    resp = await client.post(
        f"/api/sessions/{session['id']}/upload", files=_file("notes.txt", b"text")
    )
    assert resp.status_code == 400
    assert "Unsupported file type" in resp.json()["detail"]


async def test_upload_rejected_while_processing(
    client, make_session, set_session_status
):
    session = await make_session()
    await set_session_status(session["id"], "transcribing")
    resp = await client.post(
        f"/api/sessions/{session['id']}/upload", files=_file("a.mp3", b"audio")
    )
    assert resp.status_code == 400


async def test_upload_audio_file_dispatches_processing(
    client, make_session, upload_storage, celery_calls
):
    session = await make_session()
    resp = await client.post(
        f"/api/sessions/{session['id']}/upload", files=_file("sessao.mp3", b"audio-bytes")
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "pending"
    assert len(body["audio_files"]) == 1
    assert body["audio_files"][0]["filename"] == "sessao.mp3"
    assert body["audio_files"][0]["size"] == len(b"audio-bytes")

    # The processing chain was enqueued for this session
    assert celery_calls["process_session"] == [(session["id"],)]

    # The file landed on disk under the session's storage dir
    saved = upload_storage.list_files(session["id"])
    assert any(f.endswith("sessao.mp3") for f in saved)


async def test_upload_zip_extracts_audio_files(
    client, make_session, upload_storage, celery_calls
):
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w") as zf:
        zf.writestr("mesa.mp3", b"mesa-audio")
        zf.writestr("jogador.m4a", b"jogador-audio")
        zf.writestr("ler.txt", b"not audio")
    zip_bytes = bio.getvalue()

    session = await make_session()
    resp = await client.post(
        f"/api/sessions/{session['id']}/upload", files=_file("arquivos.zip", zip_bytes)
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert {f["filename"] for f in body["audio_files"]} == {"mesa.mp3", "jogador.m4a"}
    # Two audio entries + the ZIP extraction log line
    steps = [log["step"] for log in body["processing_logs"]]
    assert steps.count("upload") >= 1


async def test_upload_zip_without_audio_rejected(client, make_session, upload_storage):
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w") as zf:
        zf.writestr("apenas.txt", b"no audio here")
    session = await make_session()
    resp = await client.post(
        f"/api/sessions/{session['id']}/upload",
        files=_file("vazio.zip", bio.getvalue()),
    )
    assert resp.status_code == 400
    assert "No audio files found" in resp.json()["detail"]


async def test_upload_appends_to_existing_files(
    client, make_session, upload_storage, celery_calls
):
    session = await make_session()
    await client.post(
        f"/api/sessions/{session['id']}/upload", files=_file("a.mp3", b"primeiro")
    )
    resp = await client.post(
        f"/api/sessions/{session['id']}/upload", files=_file("b.mp3", b"segundo")
    )
    assert resp.status_code == 200
    filenames = {f["filename"] for f in resp.json()["audio_files"]}
    assert filenames == {"a.mp3", "b.mp3"}
    # Dispatched again after the second upload
    assert celery_calls["process_session"].count((session["id"],)) == 2
