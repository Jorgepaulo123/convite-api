from fastapi import APIRouter, HTTPException, status

from app.config import settings
from app.schemas import AdminLogin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login")
def admin_login(body: AdminLogin) -> dict:
    if body.password != settings.admin_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Palavra-passe incorrecta.")
    return {"ok": True}
