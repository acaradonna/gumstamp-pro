from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from ..settings import settings
from ..utils.tokens import sign_token
from ..utils.gumroad import verify_license
from ..monitoring import BusinessMetrics, tracer
from opentelemetry.trace import Status, StatusCode
from pathlib import Path
import re
import json
import time
import structlog

router = APIRouter()


SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,120}$")


class CreateConfigResponse(BaseModel):
    product_id: str = Field(..., description="Sanitized product identifier")
    download_template: str


@router.post("/upload", response_model=CreateConfigResponse)
async def upload_source_pdf(
    product_id: str = Form(...),
    file: UploadFile = File(...),
    footer_text: Optional[str] = Form(default="Purchased by {email} on {date}"),
    license_key: Optional[str] = Form(default=None),
):
    logger = structlog.get_logger("gumstamp.creator")
    start_time = time.time()
    
    with tracer.start_as_current_span("upload_source_pdf") as span:
        span.set_attribute("product_id", product_id)
        span.set_attribute("has_license_key", license_key is not None)
        
        try:
            # Validate product_id
            if not SAFE_ID.match(product_id):
                BusinessMetrics.track_pdf_upload(0, 0.0, False)
                raise HTTPException(status_code=400, detail="Invalid product_id")

            # Monetization gate: if configured, verify the creator has purchased your Gumroad product
            if settings.gumroad_product_id:
                if not license_key:
                    BusinessMetrics.track_pdf_upload(0, time.time() - start_time, False)
                    raise HTTPException(status_code=402, detail="License required")
                if not verify_license(license_key, settings.gumroad_product_id):
                    BusinessMetrics.track_pdf_upload(0, time.time() - start_time, False)
                    raise HTTPException(status_code=403, detail="Invalid license")
            
            # Read and validate file
            contents = await file.read()
            file_size = len(contents)
            if file_size == 0 or file_size > 10 * 1024 * 1024:
                BusinessMetrics.track_pdf_upload(file_size, 0.0, False)
                raise HTTPException(status_code=400, detail="Invalid file size")

            # Basic PDF magic bytes check
            if not contents.startswith(b"%PDF"):
                BusinessMetrics.track_pdf_upload(file_size, 0.0, False)
                raise HTTPException(status_code=400, detail="File must be a PDF")
            
            span.set_attribute("file_size_bytes", file_size)
            
            # Save file to storage/source/{product_id}.pdf
            dest = settings.storage_dir / "source" / f"{product_id}.pdf"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(contents)

            # Persist simple config alongside source to influence stamping (demo-friendly)
            cfg_path = settings.storage_dir / "source" / f"{product_id}.json"
            try:
                cfg = {"footer_text": footer_text}
                cfg_path.write_text(json.dumps(cfg))
            except Exception as e:
                logger.warning("Failed to save config", product_id=product_id, error=str(e))
                # Non-fatal; proceed without saved config
                span.record_exception(e)

            processing_time = time.time() - start_time
            BusinessMetrics.track_pdf_upload(file_size, processing_time, True)
            
            logger.info(
                "PDF uploaded successfully",
                product_id=product_id,
                file_size=file_size,
                processing_time=processing_time
            )
            
            template = f"{settings.base_url}/download/{{token}}"
            return CreateConfigResponse(product_id=product_id, download_template=template)
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            processing_time = time.time() - start_time
            BusinessMetrics.track_pdf_upload(0, processing_time, False)
            
            logger.error(
                "PDF upload failed",
                product_id=product_id,
                error=str(e),
                processing_time=processing_time
            )
            
            span.record_exception(e)
            span.set_status(Status(status_code=StatusCode.ERROR, description=str(e)))
            raise HTTPException(status_code=500, detail="Upload failed")


class TokenRequest(BaseModel):
    product_id: str
    email: str
    sale_id: Optional[str] = None


class TokenResponse(BaseModel):
    token: str
    download_url: str


@router.post("/token", response_model=TokenResponse)
def create_token(body: TokenRequest, license_key: Optional[str] = None):
    logger = structlog.get_logger("gumstamp.creator")
    
    with tracer.start_as_current_span("create_token") as span:
        span.set_attribute("product_id", body.product_id)
        span.set_attribute("has_license_key", license_key is not None)
        span.set_attribute("has_sale_id", body.sale_id is not None)
        
        try:
            # Validate inputs
            if not SAFE_ID.match(body.product_id):
                BusinessMetrics.track_token_operation("create", False)
                raise HTTPException(status_code=400, detail="Invalid product_id")
            if not isinstance(body.email, str) or "@" not in body.email or len(body.email) > 254:
                BusinessMetrics.track_token_operation("create", False)
                raise HTTPException(status_code=400, detail="Invalid email")

            # Monetization gate
            if settings.gumroad_product_id:
                if not license_key:
                    BusinessMetrics.track_token_operation("create", False)
                    raise HTTPException(status_code=402, detail="License required")
                if not verify_license(license_key, settings.gumroad_product_id):
                    BusinessMetrics.track_token_operation("create", False)
                    raise HTTPException(status_code=403, detail="Invalid license")
            
            token = sign_token({
                "product_id": body.product_id,
                "email": body.email,
                "sale_id": body.sale_id,
            })
            
            BusinessMetrics.track_token_operation("create", True)
            
            logger.info(
                "Token created successfully",
                product_id=body.product_id,
                has_sale_id=body.sale_id is not None
            )
            
            return TokenResponse(token=token, download_url=f"{settings.base_url}/download/{token}")
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            BusinessMetrics.track_token_operation("create", False)
            
            logger.error(
                "Token creation failed",
                product_id=body.product_id,
                error=str(e)
            )
            
            span.record_exception(e)
            span.set_status(Status(status_code=StatusCode.ERROR, description=str(e)))
            raise HTTPException(status_code=500, detail="Token creation failed")
