import pytest


pytestmark = pytest.mark.asyncio


async def test_create_session_auto_increments_number_and_position(make_campaign, client):
    campaign = await make_campaign()
    s1 = await client.post(
        "/api/sessions", json={"campaign_id": campaign["id"], "title": "Primeira"}
    )
    s2 = await client.post(
        "/api/sessions", json={"campaign_id": campaign["id"], "title": "Segunda"}
    )
    assert s1.json()["session_number"] == 1
    assert s2.json()["session_number"] == 2

    # Another campaign's sessions count independently
    other = await make_campaign()
    s3 = await client.post(
        "/api/sessions", json={"campaign_id": other["id"], "title": "Outra campanha"}
    )
    assert s3.json()["session_number"] == 1


async def test_list_sessions_filters_by_campaign(make_campaign, client):
    c1 = await make_campaign()
    c2 = await make_campaign()
    await client.post("/api/sessions", json={"campaign_id": c1["id"], "title": "A"})
    await client.post("/api/sessions", json={"campaign_id": c2["id"], "title": "B"})

    resp = await client.get("/api/sessions", params={"campaign_id": c1["id"]})
    assert [s["title"] for s in resp.json()] == ["A"]

    resp = await client.get("/api/sessions")
    assert len(resp.json()) == 2


async def test_get_session_includes_processing_logs(make_campaign, client):
    campaign = await make_campaign()
    created = (
        await client.post(
            "/api/sessions", json={"campaign_id": campaign["id"], "title": "S1"}
        )
    ).json()

    resp = await client.get(f"/api/sessions/{created['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "pending"
    assert body["processing_logs"] == []


async def test_get_session_not_found(client):
    assert (await client.get("/api/sessions/9999")).status_code == 404


async def test_create_session_for_missing_campaign_fails(client):
    resp = await client.post(
        "/api/sessions", json={"campaign_id": 9999, "title": "Órfã"}
    )
    assert resp.status_code == 404


async def test_update_session_summary(client, make_session):
    session = await make_session()
    resp = await client.put(
        f"/api/sessions/{session['id']}",
        json={"final_summary": "O grupo derrotou o dragão."},
    )
    assert resp.status_code == 200
    assert resp.json()["final_summary"] == "O grupo derrotou o dragão."


async def test_delete_session(client, make_session):
    session = await make_session()
    assert (await client.delete(f"/api/sessions/{session['id']}")).status_code == 204
    assert (await client.get(f"/api/sessions/{session['id']}")).status_code == 404


class TestRetry:
    async def test_retry_rejected_when_not_in_error(self, make_session, client):
        session = await make_session()
        resp = await client.post(f"/api/sessions/{session['id']}/retry")
        assert resp.status_code == 400

    async def test_retry_without_transcription_restarts_pipeline(
        self, make_session, set_session_status, client, celery_calls
    ):
        session = await make_session()
        await set_session_status(session["id"], "error", error_message="boom")

        resp = await client.post(f"/api/sessions/{session['id']}/retry")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "pending"
        assert body["error_message"] is None
        # Restarts from transcription, not summarization
        assert celery_calls["process_session"] == [(session["id"],)]
        assert celery_calls["summarize_session"] == []

    async def test_retry_with_transcription_resumes_summarization(
        self, make_session, set_session_status, client, celery_calls
    ):
        session = await make_session()
        await set_session_status(
            session["id"],
            "error",
            error_message="LLM timeout",
            transcription="Transcrição pronta",
        )

        resp = await client.post(f"/api/sessions/{session['id']}/retry")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "summarizing"
        # Skips transcription, goes straight to summarization
        assert celery_calls["summarize_session"] == [(session["id"],)]
        assert celery_calls["process_session"] == []

    async def test_retry_not_found(self, client):
        assert (await client.post("/api/sessions/9999/retry")).status_code == 404


class TestRegenerate:
    async def test_regenerate_clears_results_and_reprocesses(
        self, make_session, set_session_status, client, celery_calls
    ):
        session = await make_session()
        await set_session_status(
            session["id"],
            "ready",
            transcription="texto antigo",
            raw_summary="resumo bruto",
            final_summary="resumo final",
        )

        resp = await client.post(f"/api/sessions/{session['id']}/regenerate")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "pending"
        assert body["transcription"] is None
        assert body["raw_summary"] is None
        assert body["final_summary"] is None
        assert celery_calls["process_session"] == [(session["id"],)]

    async def test_regenerate_allowed_in_error_state(
        self, make_session, set_session_status, client, celery_calls
    ):
        session = await make_session()
        await set_session_status(session["id"], "error", error_message="boom")
        resp = await client.post(f"/api/sessions/{session['id']}/regenerate")
        assert resp.status_code == 200

    async def test_regenerate_rejected_while_processing(
        self, make_session, set_session_status, client
    ):
        session = await make_session()
        await set_session_status(session["id"], "transcribing")
        resp = await client.post(f"/api/sessions/{session['id']}/regenerate")
        assert resp.status_code == 400

    async def test_regenerate_not_found(self, client):
        assert (await client.post("/api/sessions/9999/regenerate")).status_code == 404
