import asyncio
import json

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import settings

router = APIRouter()


@router.websocket("/ws/sessions/{session_id}")
async def session_websocket(websocket: WebSocket, session_id: int):
    await websocket.accept()

    r = aioredis.from_url(settings.REDIS_URL)
    pubsub = r.pubsub()
    channel = f"rpg:session:{session_id}"

    try:
        await pubsub.subscribe(channel)

        # Send initial connection confirmation
        await websocket.send_text(json.dumps({"type": "connected"}))

        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message and message["type"] == "message":
                await websocket.send_text(message["data"].decode())
            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await r.close()
