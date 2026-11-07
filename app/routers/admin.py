from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import Felicitation, Guest, GuestPhoto
from app.schemas import FelicitationAdmin, GuestAdmin, GuestCreate, GuestPhotoAdmin, GuestUpdate
from app.utils import allocate_random_guest_code, guest_code_from_contact, guest_to_public

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/guests", response_model=list[GuestAdmin])
def list_guests(db: Session = Depends(get_db)) -> list[GuestAdmin]:
    rows = db.query(Guest).order_by(Guest.created_at.desc()).all()
    return [
        GuestAdmin(
            id=g.id,
            contact=g.contact,
            created_at=g.created_at,
            checked_in_at=g.checked_in_at,
            **guest_to_public(g),
        )
        for g in rows
    ]


@router.post("/guests", response_model=GuestAdmin, status_code=201)
def create_guest(body: GuestCreate, db: Session = Depends(get_db)) -> GuestAdmin:
    raw_contact = (body.contact or "").strip()
    table_name = body.table.strip() if body.table and body.table.strip() else None

    if raw_contact:
        code = guest_code_from_contact(raw_contact)
        contact = raw_contact
    else:
        code = allocate_random_guest_code(db)
        contact = code

    if db.query(Guest).filter(Guest.code == code).first():
        raise HTTPException(status_code=409, detail="Já existe convidado com este código de acesso.")

    guest = Guest(
        name=body.name.strip(),
        contact=contact,
        code=code,
        table_name=table_name,
    )
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return GuestAdmin(
        id=guest.id,
        contact=guest.contact,
        created_at=guest.created_at,
        checked_in_at=guest.checked_in_at,
        **guest_to_public(guest),
    )


@router.patch("/guests/{guest_id}", response_model=GuestAdmin)
def update_guest(guest_id: int, body: GuestUpdate, db: Session = Depends(get_db)) -> GuestAdmin:
    guest = db.query(Guest).filter(Guest.id == guest_id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Convidado não encontrado.")
    if body.name is not None:
        guest.name = body.name.strip()
    if body.contact is not None:
        contact = body.contact.strip()
        code = guest_code_from_contact(contact)
        other = db.query(Guest).filter(Guest.code == code, Guest.id != guest_id).first()
        if other:
            raise HTTPException(status_code=409, detail="Já existe convidado com este número de contacto.")
        guest.contact = contact
        guest.code = code
    if body.table is not None:
        guest.table_name = body.table.strip() or None
    db.commit()
    db.refresh(guest)
    return GuestAdmin(
        id=guest.id,
        contact=guest.contact,
        created_at=guest.created_at,
        checked_in_at=guest.checked_in_at,
        **guest_to_public(guest),
    )


@router.delete("/guests/{guest_id}", status_code=204)
def delete_guest(guest_id: int, db: Session = Depends(get_db)) -> None:
    guest = db.query(Guest).filter(Guest.id == guest_id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Convidado não encontrado.")
    db.delete(guest)
    db.commit()


@router.get("/felicitacoes", response_model=list[FelicitationAdmin])
def list_felicitacoes(db: Session = Depends(get_db)) -> list[FelicitationAdmin]:
    rows = db.query(Felicitation).order_by(Felicitation.created_at.desc()).limit(100).all()
    return [FelicitationAdmin.model_validate(r) for r in rows]


@router.get("/guest-photos", response_model=list[GuestPhotoAdmin])
def list_guest_photos(db: Session = Depends(get_db)) -> list[GuestPhotoAdmin]:
    rows = db.query(GuestPhoto).order_by(GuestPhoto.created_at.desc()).limit(200).all()
    return [
        GuestPhotoAdmin(id=r.id, guest_name=r.guest_name, url=r.file_path, created_at=r.created_at) for r in rows
    ]
