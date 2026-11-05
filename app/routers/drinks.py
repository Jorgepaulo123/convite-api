from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import Drink, DrinkOrder, DrinkOrderStatus, Guest
from app.schemas import (
    DrinkOrderCreate,
    DrinkOrderOut,
    DrinkOrderStatusUpdate,
    DrinkOut,
    DrinkUpdate,
)
from app.utils import ALLOWED_IMAGE, save_upload

router = APIRouter(tags=["drinks"])
public_router = APIRouter(prefix="/drinks", tags=["drinks"])
orders_router = APIRouter(prefix="/drink-orders", tags=["drink-orders"])
admin_router = APIRouter(
    prefix="/admin/drinks",
    tags=["admin-drinks"],
    dependencies=[Depends(require_admin)],
)
admin_orders_router = APIRouter(
    prefix="/admin/drink-orders",
    tags=["admin-drink-orders"],
    dependencies=[Depends(require_admin)],
)


def _drink_out(row: Drink) -> DrinkOut:
    return DrinkOut(
        id=row.id,
        name=row.name,
        quantity=row.quantity,
        active=row.active,
        sort_order=row.sort_order,
        image_url=row.image_path,
    )


def _order_out(row: DrinkOrder) -> DrinkOrderOut:
    return DrinkOrderOut.model_validate(row)


@public_router.get("", response_model=list[DrinkOut])
def list_drinks_catalog(db: Session = Depends(get_db)) -> list[DrinkOut]:
    rows = (
        db.query(Drink)
        .filter(Drink.active.is_(True))
        .order_by(Drink.sort_order, Drink.id)
        .all()
    )
    return [_drink_out(r) for r in rows]


@orders_router.post("", response_model=DrinkOrderOut, status_code=201)
def create_drink_order(body: DrinkOrderCreate, db: Session = Depends(get_db)) -> DrinkOrderOut:
    guest = db.query(Guest).filter(Guest.code == body.code).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Convidado não encontrado.")

    drink = db.query(Drink).filter(Drink.id == body.drink_id, Drink.active.is_(True)).first()
    if not drink:
        raise HTTPException(status_code=404, detail="Bebida não disponível.")
    if drink.quantity < body.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente. Disponível: {drink.quantity}.",
        )

    drink.quantity -= body.quantity
    order = DrinkOrder(
        guest_id=guest.id,
        guest_name=guest.name,
        drink_id=drink.id,
        drink_name=drink.name,
        quantity=body.quantity,
        status=DrinkOrderStatus.pending.value,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return _order_out(order)


@orders_router.get("/staff", response_model=list[DrinkOrderOut])
def list_orders_for_staff(
    status: DrinkOrderStatus | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[DrinkOrderOut]:
    q = db.query(DrinkOrder).order_by(DrinkOrder.created_at.desc())
    if status is not None:
        q = q.filter(DrinkOrder.status == status.value)
    rows = q.limit(limit).all()
    return [_order_out(r) for r in rows]


@orders_router.patch("/{order_id}/status", response_model=DrinkOrderOut)
def update_order_status(
    order_id: int,
    body: DrinkOrderStatusUpdate,
    db: Session = Depends(get_db),
) -> DrinkOrderOut:
    order = db.query(DrinkOrder).filter(DrinkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    new_status = body.status.value
    old_status = order.status

    if new_status == old_status:
        return _order_out(order)

    if new_status == DrinkOrderStatus.cancelled.value and old_status != DrinkOrderStatus.cancelled.value:
        drink = db.query(Drink).filter(Drink.id == order.drink_id).first()
        if drink:
            drink.quantity += order.quantity

    if new_status == DrinkOrderStatus.delivered.value:
        order.delivered_at = datetime.now(timezone.utc)
    elif new_status != DrinkOrderStatus.delivered.value:
        order.delivered_at = None

    order.status = new_status
    db.commit()
    db.refresh(order)
    return _order_out(order)


@admin_router.get("", response_model=list[DrinkOut])
def admin_list_drinks(db: Session = Depends(get_db)) -> list[DrinkOut]:
    rows = db.query(Drink).order_by(Drink.sort_order, Drink.id).all()
    return [_drink_out(r) for r in rows]


@admin_router.post("", response_model=DrinkOut, status_code=201)
async def admin_create_drink(
    name: str = Form(...),
    quantity: int = Form(...),
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
) -> DrinkOut:
    if quantity < 0 or quantity > 100_000:
        raise HTTPException(status_code=400, detail="Quantidade inválida.")
    image_path = None
    if file and file.filename:
        image_path = save_upload(file, "drinks", ALLOWED_IMAGE)
    max_order = db.query(Drink).count()
    row = Drink(name=name.strip(), quantity=quantity, sort_order=max_order, image_path=image_path)
    db.add(row)
    db.commit()
    db.refresh(row)
    return _drink_out(row)


@admin_router.post("/{drink_id}/photo", response_model=DrinkOut)
async def admin_upload_drink_photo(
    drink_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DrinkOut:
    row = db.query(Drink).filter(Drink.id == drink_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Bebida não encontrada.")
    row.image_path = save_upload(file, "drinks", ALLOWED_IMAGE)
    db.commit()
    db.refresh(row)
    return _drink_out(row)


@admin_router.patch("/{drink_id}", response_model=DrinkOut)
def admin_update_drink(drink_id: int, body: DrinkUpdate, db: Session = Depends(get_db)) -> DrinkOut:
    row = db.query(Drink).filter(Drink.id == drink_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Bebida não encontrada.")
    if body.name is not None:
        row.name = body.name.strip()
    if body.quantity is not None:
        row.quantity = body.quantity
    if body.active is not None:
        row.active = body.active
    if body.sort_order is not None:
        row.sort_order = body.sort_order
    db.commit()
    db.refresh(row)
    return _drink_out(row)


@admin_router.delete("/{drink_id}", status_code=204)
def admin_delete_drink(drink_id: int, db: Session = Depends(get_db)) -> None:
    row = db.query(Drink).filter(Drink.id == drink_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Bebida não encontrada.")
    pending = (
        db.query(DrinkOrder)
        .filter(
            DrinkOrder.drink_id == drink_id,
            DrinkOrder.status == DrinkOrderStatus.pending.value,
        )
        .count()
    )
    if pending:
        raise HTTPException(
            status_code=400,
            detail="Há pedidos pendentes desta bebida. Marque-os como entregues ou cancele primeiro.",
        )
    db.delete(row)
    db.commit()


@admin_orders_router.get("", response_model=list[DrinkOrderOut])
def admin_list_orders(
    status: DrinkOrderStatus | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[DrinkOrderOut]:
    return list_orders_for_staff(status=status, limit=limit, db=db)
