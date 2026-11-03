from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import UPLOAD_DIR, settings
from app.database import Base, SessionLocal, engine
from app.routers import admin, admin_public, event, gallery, guests, interactions, program, screen, ws_screen
from app.models import GalleryItem, GuestPhoto
from app.seed import seed_event, seed_program


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_event(db)
        seed_program(db)
        existing_paths = {row.file_path for row in db.query(GalleryItem.file_path).all()}
        order = db.query(GalleryItem).count()
        for photo in db.query(GuestPhoto).order_by(GuestPhoto.created_at, GuestPhoto.id):
            if photo.file_path in existing_paths:
                continue
            db.add(GalleryItem(file_path=photo.file_path, sort_order=order))
            existing_paths.add(photo.file_path)
            order += 1
        db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="Kayan Graduation API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(guests.router, prefix="/api")
app.include_router(admin_public.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(gallery.router, prefix="/api")
app.include_router(gallery.admin_router, prefix="/api")
app.include_router(interactions.router, prefix="/api")
app.include_router(screen.router, prefix="/api")
app.include_router(screen.admin_router, prefix="/api")
app.include_router(ws_screen.router, prefix="/api")
app.include_router(program.router, prefix="/api")
app.include_router(program.admin_router, prefix="/api")
app.include_router(event.router, prefix="/api")
app.include_router(event.admin_router, prefix="/api")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
