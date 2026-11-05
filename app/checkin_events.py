from app.ws_manager import attendance_hub


async def broadcast_attendance_stats(*, checked_in: int, total_guests: int) -> None:
    if not attendance_hub.connections:
        return
    await attendance_hub.broadcast(
        {
            "type": "stats",
            "payload": {"checked_in": checked_in, "total_guests": total_guests},
        }
    )


async def broadcast_attendance_checkin(
    *,
    name: str,
    table: str | None,
    checked_in: int,
    total_guests: int,
    already_checked_in: bool,
) -> None:
    if not attendance_hub.connections:
        return
    await attendance_hub.broadcast(
        {
            "type": "checkin",
            "payload": {
                "name": name,
                "table": table,
                "checked_in": checked_in,
                "total_guests": total_guests,
                "already_checked_in": already_checked_in,
            },
        }
    )


async def broadcast_attendance_refresh(*, checked_in: int, total_guests: int) -> None:
    await broadcast_attendance_stats(checked_in=checked_in, total_guests=total_guests)
