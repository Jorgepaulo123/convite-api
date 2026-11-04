from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Felicitation, Guest, GuestPhoto, RsvpStatus
from app.schemas import FelicitationCreate, PresentAck, RsvpCreate
from app.screen_events import broadcast_message, broadcast_photo
from app.utils import guest_code_from_contact, save_guest_selfie

router = APIRouter(tags=["interactions"])


def _guest_by_code(db: Session, code: str) -> Guest:
    guest = db.query(Guest).filter(Guest.code == code).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Convidado não encontrado.")
    return guest


@router.post("/rsvp")
def submit_rsvp(body: RsvpCreate, db: Session = Depends(get_db)) -> dict:
    guest = _guest_by_code(db, body.code)
    if body.status not in (RsvpStatus.yes, RsvpStatus.no):
        raise HTTPException(status_code=400, detail="Estado de presença inválido.")
    guest.rsvp_status = body.status.value
    db.commit()
    return {"ok": True, "status": guest.rsvp_status}


@router.post("/present/ack")
def acknowledge_present(body: PresentAck, db: Session = Depends(get_db)) -> dict:
    _guest_by_code(db, body.code)
    return {"ok": True}


@router.post("/felicitacoes", status_code=201)
async def create_felicitation(body: FelicitationCreate, db: Session = Depends(get_db)) -> dict:
    guest = _guest_by_code(db, body.code)
    row = Felicitation(guest_id=guest.id, guest_name=guest.name, message=body.message.strip())
    db.add(row)
    db.commit()
    db.refresh(row)
    await broadcast_message(row, db)
    return {"ok": True, "id": row.id}


@router.post("/guest-photos", status_code=201)
async def upload_guest_photo(
    code: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    guest = _guest_by_code(db, guest_code_from_contact(code))
    url = save_guest_selfie(file)
    row = GuestPhoto(guest_id=guest.id, guest_name=guest.name, file_path=url)
    db.add(row)
    db.commit()
    db.refresh(row)
    await broadcast_photo(row, db)
    return {"ok": True, "id": row.id, "url": url}
