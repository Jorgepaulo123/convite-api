from fastapi import APIRouter, Depends, File, UploadFile

from app.routers.screen import _build_screen_state
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import GalleryItem
from app.schemas import GalleryItemOut
from app.utils import ALLOWED_IMAGE, save_upload

router = APIRouter(prefix="/gallery", tags=["gallery"])
admin_router = APIRouter(
    prefix="/admin/gallery",
    tags=["admin-gallery"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[GalleryItemOut])
def list_gallery(db: Session = Depends(get_db)) -> list[GalleryItemOut]:
    rows = db.query(GalleryItem).order_by(GalleryItem.sort_order, GalleryItem.id).all()
    return [GalleryItemOut(id=r.id, url=r.file_path, sort_order=r.sort_order) for r in rows]


@admin_router.post("", response_model=GalleryItemOut, status_code=201)
async def upload_gallery_item(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> GalleryItemOut:
    from app.screen_events import broadcast_screen_state

    url = save_upload(file, "gallery", ALLOWED_IMAGE)
    max_order = db.query(GalleryItem).count()
    item = GalleryItem(file_path=url, sort_order=max_order)
    db.add(item)
    db.commit()
    db.refresh(item)
    out = _build_screen_state(db)
    await broadcast_screen_state(out.model_dump(mode="json"))
    return GalleryItemOut(id=item.id, url=item.file_path, sort_order=item.sort_order)


@admin_router.delete("/{item_id}", status_code=204)
async def delete_gallery_item(item_id: int, db: Session = Depends(get_db)) -> None:
    from app.screen_events import broadcast_screen_state

    item = db.query(GalleryItem).filter(GalleryItem.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
        out = _build_screen_state(db)
        await broadcast_screen_state(out.model_dump(mode="json"))
