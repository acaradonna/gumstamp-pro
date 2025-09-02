from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from ..utils.tokens import verify_token
from ..settings import settings
from ..utils.pdf import stamp_pdf
import json

router = APIRouter()


@router.get("/download/{token}")
def download_token(token: str):
    data = verify_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    product_id = data.get("product_id")
    email = data.get("email")
    # Validate required fields
    if not isinstance(product_id, str) or not isinstance(email, str):
        raise HTTPException(status_code=400, detail="Token missing required fields")
    sale_id = data.get("sale_id")

    source = settings.storage_dir / "source" / f"{product_id}.pdf"
    if not source.exists():
        raise HTTPException(status_code=404, detail="Source PDF not found")

    out_dir = settings.storage_dir / "stamped" / product_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{sale_id or email}.pdf"

    if not out_file.exists():
        # Create stamped PDF on demand
        footer = f"Purchased by {email}"
        cfg_path = settings.storage_dir / "source" / f"{product_id}.json"
        if cfg_path.exists():
            try:
                cfg = json.loads(cfg_path.read_text())
                ft = cfg.get("footer_text")
                if isinstance(ft, str) and "{email}" in ft:
                    footer = ft.replace("{email}", email)
            except Exception:
                pass
        stamp_pdf(input_path=source, output_path=out_file, footer_text=footer, diagonal_text=None)

    return FileResponse(path=out_file, media_type="application/pdf", filename=out_file.name)
