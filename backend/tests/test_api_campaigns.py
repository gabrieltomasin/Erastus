import pytest


pytestmark = pytest.mark.asyncio


async def test_create_campaign(client, make_campaign):
    campaign = await make_campaign(title="A Maldição de Strahd")
    assert campaign["title"] == "A Maldição de Strahd"
    assert campaign["session_count"] == 0
    assert campaign["id"] > 0


async def test_list_campaigns_orders_by_recent_update(client, make_campaign):
    first = await make_campaign(title="Primeira")
    second = await make_campaign(title="Segunda")

    resp = await client.get("/api/campaigns")
    assert resp.status_code == 200
    titles = [c["title"] for c in resp.json()]
    assert titles == ["Segunda", "Primeira"]

    # Touching the first campaign moves it to the top of the list
    resp = await client.put(f"/api/campaigns/{first['id']}", json={"title": "Primeira atualizada"})
    assert resp.status_code == 200
    resp = await client.get("/api/campaigns")
    assert [c["title"] for c in resp.json()] == ["Primeira atualizada", "Segunda"]
    assert second["id"] != first["id"]


async def test_get_campaign_includes_sessions(client, make_campaign, make_session):
    campaign = await make_campaign()
    s1 = await make_session(campaign_id=campaign["id"], title="Sessão 1")
    s2 = await make_session(campaign_id=campaign["id"], title="Sessão 2")

    resp = await client.get(f"/api/campaigns/{campaign['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_count"] == 2
    assert [s["title"] for s in body["sessions"]] == ["Sessão 1", "Sessão 2"]
    assert {s["id"] for s in body["sessions"]} == {s1["id"], s2["id"]}


async def test_get_campaign_not_found(client):
    resp = await client.get("/api/campaigns/9999")
    assert resp.status_code == 404


async def test_update_campaign_partial(client, make_campaign):
    campaign = await make_campaign(title="Original", description="desc antiga")
    resp = await client.put(
        f"/api/campaigns/{campaign['id']}", json={"description": "desc nova"}
    )
    assert resp.status_code == 200
    body = resp.json()
    # Only the sent field changes
    assert body["description"] == "desc nova"
    assert body["title"] == "Original"


async def test_delete_campaign_cascades_sessions(client, make_campaign, make_session):
    campaign = await make_campaign()
    session = await make_session(campaign_id=campaign["id"])

    resp = await client.delete(f"/api/campaigns/{campaign['id']}")
    assert resp.status_code == 204

    assert (await client.get(f"/api/campaigns/{campaign['id']}")).status_code == 404
    assert (await client.get(f"/api/sessions/{session['id']}")).status_code == 404


async def test_reorder_sessions(client, make_campaign, make_session):
    campaign = await make_campaign()
    s1 = await make_session(campaign_id=campaign["id"], title="A")
    s2 = await make_session(campaign_id=campaign["id"], title="B")
    s3 = await make_session(campaign_id=campaign["id"], title="C")

    resp = await client.put(
        f"/api/campaigns/{campaign['id']}/sessions/reorder",
        json={"session_ids": [s3["id"], s1["id"], s2["id"]]},
    )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}

    detail = (await client.get(f"/api/campaigns/{campaign['id']}")).json()
    assert [s["id"] for s in detail["sessions"]] == [s3["id"], s1["id"], s2["id"]]


async def test_reorder_rejects_incomplete_id_list(client, make_campaign, make_session):
    campaign = await make_campaign()
    s1 = await make_session(campaign_id=campaign["id"])
    s2 = await make_session(campaign_id=campaign["id"])

    resp = await client.put(
        f"/api/campaigns/{campaign['id']}/sessions/reorder",
        json={"session_ids": [s1["id"]]},
    )
    assert resp.status_code == 400
