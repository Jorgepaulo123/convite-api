from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import ProgramItem
from app.schemas import ProgramItemCreate, ProgramItemOut, ProgramItemUpdate

router = APIRouter(prefix="/program", tags=["program"])
admin_router = APIRouter(
    prefix="/admin/program",
    tags=["admin-program"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[ProgramItemOut])
def list_program(db: Session = Depends(get_db)) -> list[ProgramItemOut]:
    rows = db.query(ProgramItem).order_by(ProgramItem.sort_order, ProgramItem.id).all()
    return [ProgramItemOut.model_validate(r) for r in rows]


@admin_router.post("", response_model=ProgramItemOut, status_code=201)
def create_program_item(body: ProgramItemCreate, db: Session = Depends(get_db)) -> ProgramItemOut:
    max_order = db.query(ProgramItem).count()
    row = ProgramItem(title=body.title.strip(), time=body.time.strip(), sort_order=max_order)
    db.add(row)
    db.commit()
    db.refresh(row)
    return ProgramItemOut.model_validate(row)


@admin_router.patch("/{item_id}", response_model=ProgramItemOut)
def update_program_item(item_id: int, body: ProgramItemUpdate, db: Session = Depends(get_db)) -> ProgramItemOut:
    row = db.query(ProgramItem).filter(ProgramItem.id == item_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Item não encontrado.")
    if body.title is not None:
        row.title = body.title.strip()
    if body.time is not None:
        row.time = body.time.strip()
    if body.sort_order is not None:
        row.sort_order = body.sort_order
    db.commit()
    db.refresh(row)
    return ProgramItemOut.model_validate(row)


@admin_router.delete("/{item_id}", status_code=204)
def delete_program_item(item_id: int, db: Session = Depends(get_db)) -> None:
    row = db.query(ProgramItem).filter(ProgramItem.id == item_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Item não encontrado.")
    db.delete(row)
    db.commit()
