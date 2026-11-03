from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import EventInfo
from app.schemas import EventInfoOut, EventInfoUpdate

router = APIRouter(prefix="/event", tags=["event"])
admin_router = APIRouter(
    prefix="/admin/event",
    tags=["admin-event"],
    dependencies=[Depends(require_admin)],
)

DEFAULT_EVENT_DATE = "2026-11-28"


def get_event_row(db: Session) -> EventInfo:
    row = db.query(EventInfo).filter(EventInfo.id == 1).first()
    if row is None:
        row = EventInfo(id=1, event_date=DEFAULT_EVENT_DATE)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("", response_model=EventInfoOut)
def get_event_info(db: Session = Depends(get_db)) -> EventInfoOut:
    return EventInfoOut.model_validate(get_event_row(db))


@admin_router.patch("", response_model=EventInfoOut)
def update_event_info(body: EventInfoUpdate, db: Session = Depends(get_db)) -> EventInfoOut:
    row = get_event_row(db)
    row.event_date = body.event_date
    db.commit()
    db.refresh(row)
    return EventInfoOut.model_validate(row)
