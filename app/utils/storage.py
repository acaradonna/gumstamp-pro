from pathlib import Path
from ..settings import settings


def source_pdf_path(product_id: str) -> Path:
    return settings.storage_dir / "source" / f"{product_id}.pdf"


def stamped_pdf_path(product_id: str, key: str) -> Path:
    out_dir = settings.storage_dir / "stamped" / product_id
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"{key}.pdf"
