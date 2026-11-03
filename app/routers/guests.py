from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Guest
from app.schemas import CodeVerify, GuestPublic
from app.utils import guest_to_public

router = APIRouter(prefix="/guests", tags=["guests"])


def _get_by_code(db: Session, code: str) -> Guest:
    guest = db.query(Guest).filter(Guest.code == code).first()
    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convidado não encontrado.")
    return guest


@router.get("/by-code/{code}", response_model=GuestPublic)
def get_guest_by_code(code: str, db: Session = Depends(get_db)) -> GuestPublic:
    if len(code) != 6 or not code.isdigit():
        raise HTTPException(status_code=400, detail="Código inválido.")
    guest = _get_by_code(db, code)
    return GuestPublic(**guest_to_public(guest))


@router.post("/verify", response_model=GuestPublic)
def verify_code(body: CodeVerify, db: Session = Depends(get_db)) -> GuestPublic:
    guest = _get_by_code(db, body.code)
    return GuestPublic(**guest_to_public(guest))
