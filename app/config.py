from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    admin_api_key: str = "12345678"
    database_url: str = f"sqlite:///{(DATA_DIR / 'kayane.db').as_posix()}"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
    max_upload_mb: int = 15

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "kayane.db").parent.mkdir(parents=True, exist_ok=True)
(UPLOAD_DIR / "gallery").mkdir(parents=True, exist_ok=True)
(UPLOAD_DIR / "screen").mkdir(parents=True, exist_ok=True)
(UPLOAD_DIR / "screen-live").mkdir(parents=True, exist_ok=True)
(UPLOAD_DIR / "guest-photos").mkdir(parents=True, exist_ok=True)
(UPLOAD_DIR / "drinks").mkdir(parents=True, exist_ok=True)
