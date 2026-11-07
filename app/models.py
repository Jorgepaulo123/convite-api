from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
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
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    table_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    party_size: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    rsvp_status: Mapped[str] = mapped_column(String(20), default=RsvpStatus.pending.value, nullable=False)
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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


class DrinkOrderStatus(str, Enum):
    pending = "pending"
    delivered = "delivered"
    cancelled = "cancelled"


class DrinkCategory(str, Enum):
    cerveja = "CERVEJA"
    vinhos = "VINHOS"
    whisky = "WHISKY"
    champanhe = "CHAMPANHE"


class Drink(Base):
    __tablename__ = "drinks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(20), default=DrinkCategory.cerveja.value, nullable=False)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    orders: Mapped[list["DrinkOrder"]] = relationship(back_populates="drink")


class DrinkOrder(Base):
    __tablename__ = "drink_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guest_id: Mapped[int | None] = mapped_column(ForeignKey("guests.id"), nullable=True)
    guest_name: Mapped[str] = mapped_column(String(200), nullable=False)
    guest_table: Mapped[str | None] = mapped_column(String(80), nullable=True)
    drink_id: Mapped[int] = mapped_column(ForeignKey("drinks.id"), nullable=False)
    drink_name: Mapped[str] = mapped_column(String(120), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=DrinkOrderStatus.pending.value, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    drink: Mapped[Drink] = relationship(back_populates="orders")
    guest: Mapped[Guest | None] = relationship()
