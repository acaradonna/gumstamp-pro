from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from ..utils.tokens import verify_token
from ..settings import settings
from ..utils.pdf import stamp_pdf
from ..monitoring import BusinessMetrics, tracer
from opentelemetry.trace import Status, StatusCode
import json
import time
import structlog
import re
import hashlib

router = APIRouter()


@router.get("/download/{token}")
def download_token(token: str):
    logger = structlog.get_logger("gumstamp.download")
    start_time = time.time()
    
    with tracer.start_as_current_span("download_token") as span:
        try:
            # Verify token
            data = verify_token(token)
            if not data:
                BusinessMetrics.track_token_operation("verify", False)
                BusinessMetrics.track_download(False)
                raise HTTPException(status_code=401, detail="Invalid or expired token")

            BusinessMetrics.track_token_operation("verify", True)

            product_id = data.get("product_id")
            email = data.get("email")
            sale_id = data.get("sale_id")
            
            span.set_attribute("product_id", product_id or "")
            span.set_attribute("has_sale_id", sale_id is not None)
            
            # Validate required fields
            if not isinstance(product_id, str) or not isinstance(email, str):
                BusinessMetrics.track_download(False)
                raise HTTPException(status_code=400, detail="Token missing required fields")

            source = settings.storage_dir / "source" / f"{product_id}.pdf"
            if not source.exists():
                BusinessMetrics.track_download(False)
                raise HTTPException(status_code=404, detail="Source PDF not found")

            out_dir = settings.storage_dir / "stamped" / product_id
            out_dir.mkdir(parents=True, exist_ok=True)
            # Sanitize filename component
            def _safe_name(val: str) -> str:
                base = re.sub(r"[^A-Za-z0-9._-]", "_", val)[:120]
                return base or hashlib.sha1(val.encode()).hexdigest()[:12]

            name_part = _safe_name(sale_id) if isinstance(sale_id, str) and sale_id else _safe_name(email)
            out_file = out_dir / f"{name_part}.pdf"

            # Check if we need to stamp the PDF
            needs_stamping = not out_file.exists()
            
            if needs_stamping:
                stamping_start = time.time()
                
                # Create stamped PDF on demand
                footer = f"Purchased by {email}"
                cfg_path = settings.storage_dir / "source" / f"{product_id}.json"
                if cfg_path.exists():
                    try:
                        cfg = json.loads(cfg_path.read_text())
                        ft = cfg.get("footer_text")
                        if isinstance(ft, str) and "{email}" in ft:
                            footer = ft.replace("{email}", email)
                    except Exception as e:
                        logger.warning("Failed to load config", product_id=product_id, error=str(e))
                        span.record_exception(e)
                
                stamp_pdf(input_path=source, output_path=out_file, footer_text=footer, diagonal_text=None)
                
                stamping_time = time.time() - stamping_start
                BusinessMetrics.track_pdf_processing(stamping_time, True, "stamp")
                
                span.set_attribute("pdf_stamped", True)
                span.set_attribute("stamping_time", stamping_time)
            else:
                span.set_attribute("pdf_stamped", False)

            # Get file size for metrics
            file_size = out_file.stat().st_size if out_file.exists() else 0
            
            BusinessMetrics.track_download(True, file_size)
            
            total_time = time.time() - start_time
            logger.info(
                "Download successful",
                product_id=product_id,
                file_size=file_size,
                needs_stamping=needs_stamping,
                total_time=total_time
            )
            
            span.set_attribute("file_size_bytes", file_size)
            span.set_attribute("total_time", total_time)

            return FileResponse(path=out_file, media_type="application/pdf", filename=out_file.name)
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            processing_time = time.time() - start_time
            BusinessMetrics.track_download(False)
            
            logger.error(
                "Download failed",
                error=str(e),
                processing_time=processing_time
            )
            
            span.record_exception(e)
            span.set_status(Status(status_code=StatusCode.ERROR, description=str(e)))
            raise HTTPException(status_code=500, detail="Download failed")
