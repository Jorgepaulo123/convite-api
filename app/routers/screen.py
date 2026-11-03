from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import Felicitation, GalleryItem, GuestPhoto, ScreenMedia, ScreenMode, ScreenState
from app.schemas import (
    FelicitationRecent,
    ScreenLiveSlideOut,
    ScreenMediaOut,
    ScreenStateOut,
    ScreenToastMessage,
    ScreenToastPhoto,
)
from app.utils import ALLOWED_IMAGE, ALLOWED_MEDIA, media_type_from_content, save_upload

router = APIRouter(prefix="/screen", tags=["screen"])
admin_router = APIRouter(
    prefix="/admin/screen",
    tags=["admin-screen"],
    dependencies=[Depends(require_admin)],
)


def _get_state(db: Session) -> ScreenState:
    state = db.query(ScreenState).filter(ScreenState.id == 1).first()
    if not state:
        state = ScreenState(id=1, mode=ScreenMode.live.value)
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


@router.get("/recent-felicitacoes", response_model=list[FelicitationRecent])
def recent_felicitacoes(limit: int = 3, db: Session = Depends(get_db)) -> list[FelicitationRecent]:
    cap = max(1, min(limit, 50))
    rows = db.query(Felicitation).order_by(Felicitation.created_at.desc()).limit(cap).all()
    return [FelicitationRecent(id=r.id, guest_name=r.guest_name, message=r.message) for r in rows]


def _build_screen_state(db: Session) -> ScreenStateOut:
    state = _get_state(db)
    active = None
    if state.active_media_id:
        media = db.query(ScreenMedia).filter(ScreenMedia.id == state.active_media_id).first()
        if media:
            active = ScreenMediaOut(id=media.id, url=media.file_path, media_type=media.media_type)
    slides = db.query(GalleryItem).order_by(GalleryItem.sort_order, GalleryItem.id).all()
    live_slides = [ScreenLiveSlideOut(id=s.id, url=s.file_path, sort_order=s.sort_order) for s in slides]
    return ScreenStateOut(mode=ScreenMode(state.mode), active_media=active, live_slides=live_slides)


@router.get("/state", response_model=ScreenStateOut)
def get_screen_state(db: Session = Depends(get_db)) -> ScreenStateOut:
    return _build_screen_state(db)


@router.get("/next-toast")
def next_toast(db: Session = Depends(get_db)) -> ScreenToastPhoto | ScreenToastMessage | None:
    now = datetime.now(timezone.utc)
    photo = (
        db.query(GuestPhoto)
        .filter(GuestPhoto.displayed_at.is_(None))
        .order_by(GuestPhoto.created_at)
        .first()
    )
    if photo:
        photo.displayed_at = now
        db.commit()
        return ScreenToastPhoto(id=photo.id, guest_name=photo.guest_name, url=photo.file_path)

    msg = (
        db.query(Felicitation)
        .filter(Felicitation.displayed_at.is_(None))
        .order_by(Felicitation.created_at)
        .first()
    )
    if msg:
        msg.displayed_at = now
        db.commit()
        return ScreenToastMessage(id=msg.id, guest_name=msg.guest_name, message=msg.message)

    return None


@admin_router.patch("/mode/{mode}", response_model=ScreenStateOut)
async def set_screen_mode(mode: ScreenMode, db: Session = Depends(get_db)) -> ScreenStateOut:
    from app.screen_events import broadcast_screen_state

    state = _get_state(db)
    state.mode = mode.value
    db.commit()
    out = _build_screen_state(db)
    await broadcast_screen_state(out.model_dump(mode="json"))
    return out


@admin_router.post("/media", response_model=ScreenMediaOut, status_code=201)
async def upload_screen_media(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ScreenMediaOut:
    from app.screen_events import broadcast_screen_state

    url = save_upload(file, "screen", ALLOWED_MEDIA)
    mtype = media_type_from_content(file.content_type)
    media = ScreenMedia(file_path=url, media_type=mtype)
    db.add(media)
    db.commit()
    db.refresh(media)
    state = _get_state(db)
    state.active_media_id = media.id
    db.commit()
    out = _build_screen_state(db)
    await broadcast_screen_state(out.model_dump(mode="json"))
    return ScreenMediaOut(id=media.id, url=media.file_path, media_type=media.media_type)


@admin_router.get("/media", response_model=list[ScreenMediaOut])
def list_screen_media(db: Session = Depends(get_db)) -> list[ScreenMediaOut]:
    rows = db.query(ScreenMedia).order_by(ScreenMedia.created_at.desc()).limit(50).all()
    return [ScreenMediaOut(id=r.id, url=r.file_path, media_type=r.media_type) for r in rows]


@admin_router.patch("/media/{media_id}/active", response_model=ScreenStateOut)
async def set_active_media(media_id: int, db: Session = Depends(get_db)) -> ScreenStateOut:
    from app.screen_events import broadcast_screen_state

    media = db.query(ScreenMedia).filter(ScreenMedia.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media não encontrada.")
    state = _get_state(db)
    state.active_media_id = media.id
    db.commit()
    out = _build_screen_state(db)
    await broadcast_screen_state(out.model_dump(mode="json"))
    return out


