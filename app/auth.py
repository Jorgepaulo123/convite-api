from fastapi import Header, HTTPException, status

from app.config import settings


def require_admin(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")) -> None:
    if not x_admin_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Chave de admin inválida.")
