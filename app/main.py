from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import UPLOAD_DIR, settings
from app.database import Base, SessionLocal, engine
from app.routers import admin, admin_public, event, gallery, guests, interactions, program, screen, ws_screen
from app.seed import seed_event, seed_program


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_event(db)
        seed_program(db)
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
