import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.database import SessionLocal
from app.routers.screen import _build_screen_state
from app.ws_manager import screen_hub

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/screen")
async def screen_websocket(websocket: WebSocket) -> None:
    await screen_hub.connect(websocket)
    db = SessionLocal()
    try:
        snapshot = _build_screen_state(db)
        await websocket.send_text(
            json.dumps(
                {"type": "state", "payload": snapshot.model_dump(mode="json")},
                ensure_ascii=False,
            )
        )
    finally:
        db.close()
    try:
        while True:
            msg = await websocket.receive_text()
            if msg.strip().lower() == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        screen_hub.disconnect(websocket)
