from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Felicitation, GuestPhoto
from app.ws_manager import screen_hub


async def broadcast_photo(row: GuestPhoto, db: Session) -> None:
    if not screen_hub.connections:
        return
    await screen_hub.broadcast(
        {
            "type": "toast",
            "payload": {
                "kind": "photo",
                "id": row.id,
                "guest_name": row.guest_name,
                "url": row.file_path,
            },
        }
    )
    row.displayed_at = datetime.now(timezone.utc)
    db.commit()


async def broadcast_message(row: Felicitation, db: Session) -> None:
    if not screen_hub.connections:
        return
    await screen_hub.broadcast(
        {
            "type": "toast",
            "payload": {
                "kind": "message",
                "id": row.id,
                "guest_name": row.guest_name,
                "message": row.message,
            },
        }
    )
    row.displayed_at = datetime.now(timezone.utc)
    db.commit()


async def broadcast_screen_state(payload: dict) -> None:
    await screen_hub.broadcast({"type": "state", "payload": payload})
