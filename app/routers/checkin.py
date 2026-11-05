from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.checkin_events import broadcast_attendance_checkin, broadcast_attendance_refresh
from app.database import get_db
from app.models import Guest
from app.schemas import (
    AttendanceStats,
    CheckinRecent,
    CheckinResult,
    CheckinRoster,
    CheckinRosterGuest,
    CodeVerify,
)
from app.utils import guest_code_from_contact

router = APIRouter(prefix="/checkin", tags=["checkin"])


@router.post("", response_model=CheckinResult)
async def register_checkin(body: CodeVerify, db: Session = Depends(get_db)) -> CheckinResult:
    try:
        code = guest_code_from_contact(body.code)
    except HTTPException:
        return CheckinResult(
            ok=False,
            on_list=False,
            message="Introduza um número de telemóvel válido (mín. 8 dígitos).",
        )

    guest = db.query(Guest).filter(Guest.code == code).first()
    if not guest:
        return CheckinResult(
            ok=False,
            on_list=False,
            message="Este número não está na lista de convidados.",
        )

    already = guest.checked_in_at is not None
    if not already:
        guest.checked_in_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(guest)

    total = db.query(Guest).count()
    checked = db.query(Guest).filter(Guest.checked_in_at.isnot(None)).count()
    await broadcast_attendance_checkin(
        name=guest.name,
        table=guest.table_name,
        checked_in=checked,
        total_guests=total,
        already_checked_in=already,
    )

    return CheckinResult(
        ok=True,
        on_list=True,
        name=guest.name,
        table=guest.table_name,
        already_checked_in=already,
        message="Presença registada. Bem-vindo(a)!" if not already else "Entrada já registada anteriormente.",
    )


@router.post("/uncheck", response_model=CheckinResult)
async def uncheck_presence(body: CodeVerify, db: Session = Depends(get_db)) -> CheckinResult:
    try:
        code = guest_code_from_contact(body.code)
    except HTTPException:
        return CheckinResult(
            ok=False,
            on_list=False,
            message="Introduza um número de telemóvel válido (mín. 8 dígitos).",
        )

    guest = db.query(Guest).filter(Guest.code == code).first()
    if not guest:
        return CheckinResult(
            ok=False,
            on_list=False,
            message="Este número não está na lista de convidados.",
        )

    if guest.checked_in_at is None:
        return CheckinResult(
            ok=True,
            on_list=True,
            name=guest.name,
            table=guest.table_name,
            already_checked_in=False,
            message="Este convidado ainda não tinha entrada registada.",
        )

    guest.checked_in_at = None
    db.commit()
    db.refresh(guest)

    total = db.query(Guest).count()
    checked = db.query(Guest).filter(Guest.checked_in_at.isnot(None)).count()
    await broadcast_attendance_refresh(checked_in=checked, total_guests=total)

    return CheckinResult(
        ok=True,
        on_list=True,
        name=guest.name,
        table=guest.table_name,
        already_checked_in=False,
        message="Entrada removida.",
    )


@router.get("/stats", response_model=AttendanceStats)
def attendance_stats(db: Session = Depends(get_db)) -> AttendanceStats:
    total = db.query(Guest).count()
    checked = db.query(Guest).filter(Guest.checked_in_at.isnot(None)).count()
    present_rows = (
        db.query(Guest)
        .filter(Guest.checked_in_at.isnot(None))
        .order_by(Guest.checked_in_at.desc())
        .all()
    )
    present_guests = [
        CheckinRecent(name=g.name, table=g.table_name, checked_in_at=g.checked_in_at)
        for g in present_rows
        if g.checked_in_at is not None
    ]
    recent = present_guests[:15]
    return AttendanceStats(
        total_guests=total,
        checked_in=checked,
        remaining=max(0, total - checked),
        recent=recent,
        present_guests=present_guests,
    )


@router.get("/roster", response_model=CheckinRoster)
def checkin_roster(db: Session = Depends(get_db)) -> CheckinRoster:
    rows = db.query(Guest).order_by(Guest.name.asc()).all()
    checked = sum(1 for g in rows if g.checked_in_at is not None)
    return CheckinRoster(
        total_guests=len(rows),
        checked_in=checked,
        guests=[
            CheckinRosterGuest(
                name=g.name,
                table=g.table_name,
                code=g.code,
                checked_in_at=g.checked_in_at,
            )
            for g in rows
        ],
    )
