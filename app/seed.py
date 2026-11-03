from sqlalchemy.orm import Session

from app.models import EventInfo, ProgramItem

DEFAULT_EVENT_DATE = "2026-11-28"


def seed_event(db: Session) -> None:
    if db.query(EventInfo).count() > 0:
        return
    db.add(EventInfo(id=1, event_date=DEFAULT_EVENT_DATE))
    db.commit()


def seed_program(db: Session) -> None:
    if db.query(ProgramItem).count() > 0:
        return
    defaults = [
        ("Cerimónia", "16H00", 0),
        ("Cocktail", "18H00", 1),
        ("Jantar & Dança", "19H30", 2),
    ]
    for title, time, sort_order in defaults:
        db.add(ProgramItem(title=title, time=time, sort_order=sort_order))
    db.commit()
