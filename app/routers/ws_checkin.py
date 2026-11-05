import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Guest
from app.ws_manager import attendance_hub

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/checkin")
async def checkin_websocket(websocket: WebSocket) -> None:
    await attendance_hub.connect(websocket)
    db: Session = SessionLocal()
    try:
        total = db.query(Guest).count()
        checked = db.query(Guest).filter(Guest.checked_in_at.isnot(None)).count()
        await websocket.send_text(
            json.dumps(
                {
                    "type": "stats",
                    "payload": {"checked_in": checked, "total_guests": total},
                },
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
        attendance_hub.disconnect(websocket)
