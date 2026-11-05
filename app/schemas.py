from datetime import datetime

from pydantic import BaseModel, Field

from app.models import RsvpStatus, ScreenMode


class GuestPublic(BaseModel):
    code: str
    name: str
    table: str | None = None
    rsvp_status: RsvpStatus = RsvpStatus.pending

    model_config = {"from_attributes": True}


class GuestAdmin(GuestPublic):
    id: int
    contact: str
    created_at: datetime
    checked_in_at: datetime | None = None


class AdminLogin(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class GuestCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    contact: str = Field(min_length=1, max_length=120)
    table: str | None = Field(default=None, max_length=80)


class GuestUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    contact: str | None = Field(default=None, max_length=120)
    table: str | None = Field(default=None, max_length=80)


class CodeVerify(BaseModel):
    code: str = Field(min_length=8, max_length=15, pattern=r"^\d{8,15}$")


class RsvpCreate(BaseModel):
    code: str = Field(min_length=8, max_length=15, pattern=r"^\d{8,15}$")
    status: RsvpStatus


class FelicitationCreate(BaseModel):
    code: str = Field(min_length=8, max_length=15, pattern=r"^\d{8,15}$")
    message: str = Field(min_length=1, max_length=2000)


class FelicitationAdmin(BaseModel):
    id: int
    guest_name: str
    message: str
    created_at: datetime
    displayed_at: datetime | None

    model_config = {"from_attributes": True}


class FelicitationRecent(BaseModel):
    id: int
    guest_name: str
    message: str


class GuestPhotoAdmin(BaseModel):
    id: int
    guest_name: str
    url: str
    created_at: datetime


class GalleryItemOut(BaseModel):
    id: int
    url: str
    sort_order: int

    model_config = {"from_attributes": True}


class ScreenMediaOut(BaseModel):
    id: int
    url: str
    media_type: str

    model_config = {"from_attributes": True}


class ScreenLiveSlideOut(BaseModel):
    id: int
    url: str
    sort_order: int

    model_config = {"from_attributes": True}


class ScreenStateOut(BaseModel):
    mode: ScreenMode
    active_media: ScreenMediaOut | None = None
    live_slides: list[ScreenLiveSlideOut] = []


class ScreenToastPhoto(BaseModel):
    kind: str = "photo"
    id: int
    guest_name: str
    url: str


class ScreenToastMessage(BaseModel):
    kind: str = "message"
    id: int
    guest_name: str
    message: str


ScreenToast = ScreenToastPhoto | ScreenToastMessage


class PresentAck(BaseModel):
    code: str = Field(min_length=8, max_length=15, pattern=r"^\d{8,15}$")


class EventInfoOut(BaseModel):
    event_date: str

    model_config = {"from_attributes": True}


class EventInfoUpdate(BaseModel):
    event_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")


class ProgramItemOut(BaseModel):
    id: int
    title: str
    time: str
    sort_order: int

    model_config = {"from_attributes": True}


class ProgramItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    time: str = Field(min_length=1, max_length=40)


class ProgramItemUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    time: str | None = Field(default=None, max_length=40)
    sort_order: int | None = None


class CheckinResult(BaseModel):
    ok: bool
    on_list: bool
    name: str | None = None
    table: str | None = None
    already_checked_in: bool = False
    message: str


class CheckinRecent(BaseModel):
    name: str
    table: str | None = None
    checked_in_at: datetime


class AttendanceStats(BaseModel):
    total_guests: int
    checked_in: int
    remaining: int
    recent: list[CheckinRecent]


class CheckinRosterGuest(BaseModel):
    name: str
    table: str | None = None
    code: str
    checked_in_at: datetime | None = None


class CheckinRoster(BaseModel):
    total_guests: int
    checked_in: int
    guests: list[CheckinRosterGuest]
