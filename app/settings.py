from pydantic import BaseModel
from pathlib import Path
import os


class Settings(BaseModel):
    secret_key: str = os.getenv("SECRET_KEY", "dev_secret")
    storage_dir: Path = Path(os.getenv("STORAGE_DIR", "./storage")).resolve()
    base_url: str = os.getenv("BASE_URL", "http://localhost:8000")
    gumroad_product_id: str | None = os.getenv("GUMROAD_PRODUCT_ID")
    allowed_origins: list[str] = (
        [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]
        if os.getenv("ALLOWED_ORIGINS")
        else ["*"]
    )
    
    # Monitoring settings
    sentry_dsn: str | None = os.getenv("SENTRY_DSN")
    environment: str = os.getenv("ENVIRONMENT", "production")
    enable_tracing: bool = os.getenv("ENABLE_TRACING", "true").lower() == "true"
    enable_metrics: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"


settings = Settings()
settings.storage_dir.mkdir(parents=True, exist_ok=True)
(settings.storage_dir / "source").mkdir(parents=True, exist_ok=True)
(settings.storage_dir / "stamped").mkdir(parents=True, exist_ok=True)
