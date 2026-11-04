import secrets
import uuid
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image, ImageOps
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR, settings
from app.models import Guest

ALLOWED_IMAGE = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO = {"video/mp4", "video/webm", "video/quicktime"}
ALLOWED_MEDIA = ALLOWED_IMAGE | ALLOWED_VIDEO

# Selfies na /tela: redimensionar e JPEG para carregar rápido no projetor.
GUEST_SELFIE_MAX_EDGE = 1280
GUEST_SELFIE_JPEG_QUALITY = 82


def generate_guest_code(db: Session) -> str:
    for _ in range(200):
        code = f"{secrets.randbelow(10**6):06d}"
        if db.query(Guest).filter(Guest.code == code).first() is None:
            return code
    raise HTTPException(status_code=500, detail="Não foi possível gerar código único.")


def guest_to_public(g: Guest) -> dict:
    return {
        "code": g.code,
        "name": g.name,
        "table": g.table_name,
        "rsvp_status": g.rsvp_status,
    }


def save_upload(file: UploadFile, subdir: str, allowed: set[str] | None = None) -> str:
    if not file.content_type or (allowed and file.content_type not in allowed):
        raise HTTPException(status_code=400, detail="Tipo de ficheiro não permitido.")

    ext = Path(file.filename or "file").suffix.lower()
    if not ext or len(ext) > 8:
        ext = ".jpg" if file.content_type and file.content_type.startswith("image/") else ".bin"

    dest_dir = UPLOAD_DIR / subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    path = dest_dir / name

    data = file.file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"Ficheiro excede {settings.max_upload_mb}MB.")

    path.write_bytes(data)
    return f"/uploads/{subdir}/{name}"


def save_guest_selfie(file: UploadFile) -> str:
    """Guarda selfie comprimida (JPEG, max ~1280px) — só para /tela e admin, não galeria."""
    if not file.content_type or file.content_type not in ALLOWED_IMAGE:
        raise HTTPException(status_code=400, detail="Tipo de ficheiro não permitido.")

    data = file.file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"Ficheiro excede {settings.max_upload_mb}MB.")

    try:
        img = Image.open(BytesIO(data))
        img = ImageOps.exif_transpose(img)
        if img.mode != "RGB":
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                img = img.convert("RGBA")
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            else:
                img = img.convert("RGB")

        w, h = img.size
        longest = max(w, h)
        if longest > GUEST_SELFIE_MAX_EDGE:
            scale = GUEST_SELFIE_MAX_EDGE / longest
            img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)

        dest_dir = UPLOAD_DIR / "guest-photos"
        dest_dir.mkdir(parents=True, exist_ok=True)
        name = f"{uuid.uuid4().hex}.jpg"
        path = dest_dir / name
        img.save(path, "JPEG", quality=GUEST_SELFIE_JPEG_QUALITY, optimize=True)
    except OSError as exc:
        raise HTTPException(status_code=400, detail="Imagem inválida ou corrompida.") from exc

    return f"/uploads/guest-photos/{name}"


def media_type_from_content(content_type: str | None) -> str:
    if content_type and content_type.startswith("video/"):
        return "video"
    return "image"
