from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RsvpStatus(str, Enum):
    pending = "pending"
    yes = "yes"
    no = "no"


class ScreenMode(str, Enum):
    live = "live"
    photos = "photos"
    dance = "dance"
    brindes = "brindes"


class ToastKind(str, Enum):
    photo = "photo"
    message = "message"


class Guest(Base):
    __tablename__ = "guests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(6), unique=True, index=True, nullable=False)
    table_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    rsvp_status: Mapped[str] = mapped_column(String(20), default=RsvpStatus.pending.value, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    felicitacoes: Mapped[list["Felicitation"]] = relationship(back_populates="guest")
    guest_photos: Mapped[list["GuestPhoto"]] = relationship(back_populates="guest")


class GalleryItem(Base):
    __tablename__ = "gallery_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScreenMedia(Base):
    __tablename__ = "screen_media"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    media_type: Mapped[str] = mapped_column(String(20), default="image")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScreenLiveSlide(Base):
    __tablename__ = "screen_live_slides"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Felicitation(Base):
    __tablename__ = "felicitacoes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guest_id: Mapped[int | None] = mapped_column(ForeignKey("guests.id"), nullable=True)
    guest_name: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    displayed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    guest: Mapped[Guest | None] = relationship(back_populates="felicitacoes")


class GuestPhoto(Base):
    __tablename__ = "guest_photos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guest_id: Mapped[int | None] = mapped_column(ForeignKey("guests.id"), nullable=True)
    guest_name: Mapped[str] = mapped_column(String(200), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    displayed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    guest: Mapped[Guest | None] = relationship(back_populates="guest_photos")


class EventInfo(Base):
    __tablename__ = "event_info"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    event_date: Mapped[str] = mapped_column(String(10), nullable=False)


class ProgramItem(Base):
    __tablename__ = "program_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    time: Mapped[str] = mapped_column(String(40), nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScreenState(Base):
    __tablename__ = "screen_state"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    mode: Mapped[str] = mapped_column(String(20), default=ScreenMode.live.value)
    active_media_id: Mapped[int | None] = mapped_column(ForeignKey("screen_media.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
