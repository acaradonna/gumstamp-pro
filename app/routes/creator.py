from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..settings import settings
from ..utils.tokens import sign_token
from ..utils.gumroad import verify_license
import json

router = APIRouter()


class CreateConfigResponse(BaseModel):
    product_id: str
    source_key: str
    download_template: str


@router.post("/upload", response_model=CreateConfigResponse)
async def upload_source_pdf(
    product_id: str = Form(...),
    file: UploadFile = File(...),
    footer_text: Optional[str] = Form(default="Purchased by {email} on {date}"),
    license_key: Optional[str] = Form(default=None),
):
    # Monetization gate: if configured, verify the creator has purchased your Gumroad product
    if settings.gumroad_product_id:
        if not license_key:
            raise HTTPException(status_code=402, detail="License required")
        if not verify_license(license_key, settings.gumroad_product_id):
            raise HTTPException(status_code=403, detail="Invalid license")
    # Save file to storage/source/{product_id}.pdf
    dest = settings.storage_dir / "source" / f"{product_id}.pdf"
    dest.parent.mkdir(parents=True, exist_ok=True)
    contents = await file.read()
    dest.write_bytes(contents)

    # Persist simple config alongside source to influence stamping (demo-friendly)
    cfg_path = settings.storage_dir / "source" / f"{product_id}.json"
    try:
        cfg = {"footer_text": footer_text}
        cfg_path.write_text(json.dumps(cfg))
    except Exception:
        # Non-fatal; proceed without saved config
        pass

    template = f"{settings.base_url}/download/{{token}}"
    return CreateConfigResponse(product_id=product_id, source_key=str(dest), download_template=template)


class TokenRequest(BaseModel):
    product_id: str
    email: str
    sale_id: Optional[str] = None


class TokenResponse(BaseModel):
    token: str
    download_url: str


@router.post("/token", response_model=TokenResponse)
def create_token(body: TokenRequest, license_key: Optional[str] = None):
    # Monetization gate
    if settings.gumroad_product_id:
        if not license_key:
            raise HTTPException(status_code=402, detail="License required")
        if not verify_license(license_key, settings.gumroad_product_id):
            raise HTTPException(status_code=403, detail="Invalid license")
    token = sign_token({
        "product_id": body.product_id,
        "email": body.email,
        "sale_id": body.sale_id,
    })
    return TokenResponse(token=token, download_url=f"{settings.base_url}/download/{token}")
