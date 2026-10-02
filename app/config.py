"""Central configuration. All secrets come from environment variables / .env (never hard-coded)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


class Settings:
    def __init__(self) -> None:
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
        self.gemini_fallback_models: list[str] = _csv(
            os.getenv("GEMINI_FALLBACK_MODELS", "gemini-2.0-flash-lite,gemini-1.5-flash")
        )
        self.secret_key: str = os.getenv("SECRET_KEY", "dev-only-insecure-key-change-me")
        self.token_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
        db = os.getenv("DATABASE_PATH", "pocketsmart.db")
        self.database_path: str = db if os.path.isabs(db) else str(BASE_DIR / db)
        self.templates_dir: str = str(BASE_DIR / "templates")
        self.static_dir: str = str(BASE_DIR / "static")
        self.max_image_bytes: int = 5 * 1024 * 1024  # 5 MB upload limit

    @property
    def gemini_models(self) -> list[str]:
        """Primary model followed by fallbacks, without duplicates."""
        out: list[str] = []
        for m in [self.gemini_model, *self.gemini_fallback_models]:
            if m and m not in out:
                out.append(m)
        return out


def get_settings() -> Settings:
    # Re-read each call so tests can monkeypatch environment variables.
    return Settings()
