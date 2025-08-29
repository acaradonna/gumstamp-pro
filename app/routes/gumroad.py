from fastapi import APIRouter, Form
from typing import Optional
from ..utils.tokens import sign_token
from ..settings import settings

router = APIRouter()

@router.post("/ping")
async def gumroad_ping(
    sale_id: Optional[str] = Form(default=None),
    product_id: Optional[str] = Form(default=None),
    product_name: Optional[str] = Form(default=None),
    email: Optional[str] = Form(default=None),
    full_name: Optional[str] = Form(default=None),
    price: Optional[int] = Form(default=None),
    currency: Optional[str] = Form(default=None),
    quantity: Optional[int] = Form(default=None),
    license_key: Optional[str] = Form(default=None),
):
    # Minimal: accept ping and return a signed download token. Future: enqueue pre-stamp task.
    payload = {
        "sale_id": sale_id,
        "product_id": product_id,
        "email": email,
    }
    token = sign_token(payload)
    download_url = f"{settings.base_url}/download/{token}"
    return {
        "ok": True,
        "sale_id": sale_id,
        "product_id": product_id,
        "email": email,
        "token": token,
        "download_url": download_url,
    }
