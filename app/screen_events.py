from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Felicitation, GuestPhoto
from app.ws_manager import screen_hub


async def broadcast_photo(row: GuestPhoto, db: Session) -> None:
    row.displayed_at = datetime.now(timezone.utc)
    db.commit()
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


async def broadcast_message(row: Felicitation, db: Session) -> None:
    row.displayed_at = datetime.now(timezone.utc)
    db.commit()
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


async def broadcast_screen_state(payload: dict) -> None:
    await screen_hub.broadcast({"type": "state", "payload": payload})
