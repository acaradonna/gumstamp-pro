"""
Comprehensive monitoring and observability configuration for Gumstamp.
Includes OpenTelemetry, structured logging, business metrics, and health checks.
"""

import os
import time
import psutil
import structlog
import sentry_sdk
from typing import Dict, Any, Optional
from pathlib import Path
from contextlib import asynccontextmanager

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.metrics import Observation

from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .settings import settings


class MonitoringConfig:
    """Configuration for monitoring and observability"""
    
    def __init__(self):
        self.service_name = "gumstamp"
        self.service_version = os.getenv("GIT_SHA", "dev")
        self.environment = os.getenv("ENVIRONMENT", "production")
        
        # External service configurations
        self.sentry_dsn = os.getenv("SENTRY_DSN")
        self.otlp_endpoint = os.getenv("OTLP_ENDPOINT", "https://otlp.grafana.com/otlp")
        self.otlp_headers = {
            "Authorization": f"Basic {os.getenv('GRAFANA_CLOUD_API_KEY', '')}"
        } if os.getenv('GRAFANA_CLOUD_API_KEY') else {}
        
        # Monitoring feature flags
        self.enable_tracing = os.getenv("ENABLE_TRACING", "true").lower() == "true"
        self.enable_metrics = os.getenv("ENABLE_METRICS", "true").lower() == "true"
        self.enable_sentry = bool(self.sentry_dsn)
        
        # Performance thresholds
        self.slow_request_threshold = float(os.getenv("SLOW_REQUEST_THRESHOLD", "2.0"))
        self.error_rate_threshold = float(os.getenv("ERROR_RATE_THRESHOLD", "5.0"))


config = MonitoringConfig()

# Tracer is safe to obtain at import time; provider will be set on startup
tracer = trace.get_tracer(__name__)

# Metrics instruments (initialized in setup_opentelemetry after provider is configured)
_meter = None
pdf_operations_counter = None
pdf_processing_time = None
upload_file_size = None
download_counter = None
token_operations_counter = None

# Observable gauges are registered during setup
_observable_registered = False


def setup_logging():
    """Configure structured logging with JSON output"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def setup_sentry():
    """Initialize Sentry for error tracking and performance monitoring"""
    if not config.enable_sentry:
        return
        
    sentry_sdk.init(
        dsn=config.sentry_dsn,
        environment=config.environment,
        release=config.service_version,
        integrations=[
            FastApiIntegration(),
            StarletteIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        profiles_sample_rate=0.1,  # 10% for profiling
        attach_stacktrace=True,
        send_default_pii=False,  # Don't send PII
    )


def setup_opentelemetry():
    """Initialize OpenTelemetry tracing and metrics"""
    if not (config.enable_tracing or config.enable_metrics):
        return
        
    # Set up tracing
    if config.enable_tracing:
        trace.set_tracer_provider(TracerProvider())
        
        if config.otlp_endpoint and config.otlp_headers:
            otlp_exporter = OTLPSpanExporter(
                endpoint=f"{config.otlp_endpoint}/v1/traces",
                headers=config.otlp_headers
            )
            span_processor = BatchSpanProcessor(otlp_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
        # Re-create tracer using configured provider
        global tracer
        tracer = trace.get_tracer(__name__)
    
    # Set up metrics
    if config.enable_metrics:
        metric_reader = None
        if config.otlp_endpoint and config.otlp_headers:
            metric_exporter = OTLPMetricExporter(
                endpoint=f"{config.otlp_endpoint}/v1/metrics",
                headers=config.otlp_headers
            )
            metric_reader = PeriodicExportingMetricReader(
                exporter=metric_exporter,
                export_interval_millis=30000  # Export every 30 seconds
            )
            
        metrics.set_meter_provider(MeterProvider(
            metric_readers=[metric_reader] if metric_reader else []
        ))

        # Create meter and instruments AFTER provider is set
        global _meter, pdf_operations_counter, pdf_processing_time, upload_file_size, download_counter, token_operations_counter, _observable_registered
        _meter = metrics.get_meter("gumstamp")

        # Business instruments
        pdf_operations_counter = _meter.create_counter(
            name="gumstamp_pdf_operations_total",
            description="Total number of PDF operations",
            unit="1"
        )
        pdf_processing_time = _meter.create_histogram(
            name="gumstamp_pdf_processing_seconds",
            description="Time spent processing PDFs",
            unit="s"
        )
        upload_file_size = _meter.create_histogram(
            name="gumstamp_upload_file_size_bytes",
            description="Size of uploaded PDF files",
            unit="bytes"
        )
        download_counter = _meter.create_counter(
            name="gumstamp_downloads_total",
            description="Total number of successful downloads",
            unit="1"
        )
        token_operations_counter = _meter.create_counter(
            name="gumstamp_token_operations_total",
            description="Total number of token operations",
            unit="1"
        )

        # Observable gauges for system metrics
        def _observe_cpu(options):
            try:
                val = psutil.cpu_percent(interval=0.0)
                return [Observation(val, {})]
            except Exception:
                return []

        def _observe_memory(options):
            try:
                mem = psutil.virtual_memory()
                return [
                    Observation(mem.used, {"type": "used"}),
                    Observation(mem.available, {"type": "available"}),
                ]
            except Exception:
                return []

        def _observe_disk(options):
            try:
                if settings.storage_dir.exists():
                    d = psutil.disk_usage(str(settings.storage_dir))
                    return [
                        Observation(d.used, {"type": "used"}),
                        Observation(d.free, {"type": "free"}),
                    ]
                return []
            except Exception:
                return []

        _meter.create_observable_gauge(
            name="gumstamp_system_cpu_percent",
            callbacks=[_observe_cpu],
            description="System CPU usage percentage",
            unit="%",
        )
        _meter.create_observable_gauge(
            name="gumstamp_system_memory_bytes",
            callbacks=[_observe_memory],
            description="System memory usage in bytes",
            unit="bytes",
        )
        _meter.create_observable_gauge(
            name="gumstamp_storage_disk_bytes",
            callbacks=[_observe_disk],
            description="Storage disk usage in bytes",
            unit="bytes",
        )
        _observable_registered = True


def setup_auto_instrumentation():
    """Set up automatic instrumentation for FastAPI and requests"""
    if config.enable_tracing:
        # Auto-instrument FastAPI
        # Instantiate the instrumentor; instrument() patches FastAPI globally
        try:
            FastAPIInstrumentor().instrument()
        except TypeError:
            # Fallback for versions requiring explicit app-level instrumentation
            # We'll rely on ASGI/Logging instrumentation if needed
            pass
        
        # Auto-instrument HTTP requests
        try:
            RequestsInstrumentor().instrument()
        except TypeError:
            pass
        
    # Auto-instrument logging without altering our structlog formatting
    LoggingInstrumentor().instrument(set_logging_format=False)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Custom middleware for detailed request/response monitoring"""
    
    def __init__(self, app, logger=None):
        super().__init__(app)
        self.logger = logger or structlog.get_logger("gumstamp.middleware")
        self.start_time = time.time()
        
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Extract request details
        method = request.method
        path = request.url.path
        user_agent = request.headers.get("user-agent", "")
        content_length = request.headers.get("content-length", 0)
        
        try:
            content_length = int(content_length) if content_length else 0
        except (ValueError, TypeError):
            content_length = 0
            
        # Process request
        response = await call_next(request)
        
        # Calculate metrics
        duration = time.time() - start_time
        status_code = response.status_code
        
        # Log request details
        log_data = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration": duration,
            "content_length": content_length,
            "user_agent": user_agent[:100],  # Truncate user agent
        }
        
        if duration > config.slow_request_threshold:
            self.logger.warning("Slow request detected", **log_data)
        elif 400 <= status_code < 600:
            self.logger.warning("Error response", **log_data)
        else:
            self.logger.info("Request processed", **log_data)
            
        return response


class BusinessMetrics:
    """Business-specific metrics collection"""
    
    @staticmethod
    def track_pdf_upload(file_size: int, processing_time: float, success: bool):
        """Track PDF upload metrics"""
        labels = {"operation": "upload", "success": str(success).lower()}
        
        if pdf_operations_counter:
            pdf_operations_counter.add(1, labels)
        if upload_file_size:
            upload_file_size.record(file_size, labels)
        
        if success and pdf_processing_time:
            pdf_processing_time.record(processing_time, labels)
    
    @staticmethod
    def track_pdf_processing(processing_time: float, success: bool, operation: str = "stamp"):
        """Track PDF processing metrics"""
        labels = {"operation": operation, "success": str(success).lower()}
        
        if pdf_operations_counter:
            pdf_operations_counter.add(1, labels)
        if success and pdf_processing_time:
            pdf_processing_time.record(processing_time, labels)
    
    @staticmethod
    def track_download(success: bool, file_size: Optional[int] = None):
        """Track download metrics"""
        labels = {"success": str(success).lower()}
        
        if download_counter:
            download_counter.add(1, labels)
    
    @staticmethod
    def track_token_operation(operation: str, success: bool):
        """Track token operations"""
        labels = {"operation": operation, "success": str(success).lower()}
        
        if token_operations_counter:
            token_operations_counter.add(1, labels)


class SystemMetrics:
    """System resource metrics collection (kept for compatibility)."""

    @staticmethod
    def collect_system_metrics():
        """No-op: system metrics are collected via ObservableGauges callbacks."""
        return


def get_health_status() -> Dict[str, Any]:
    """Get comprehensive health status"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Storage check
        storage_healthy = True
        storage_info = {}
        if settings.storage_dir.exists():
            disk_usage = psutil.disk_usage(str(settings.storage_dir))
            storage_info = {
                "total": disk_usage.total,
                "used": disk_usage.used,
                "free": disk_usage.free,
                "percent": (disk_usage.used / disk_usage.total) * 100
            }
            storage_healthy = storage_info["percent"] < 90  # Alert at 90% usage
        
        # Overall health status
        status = "healthy"
        if cpu_percent > 90:
            status = "degraded"
        if memory.percent > 90:
            status = "degraded"
        if not storage_healthy:
            status = "unhealthy"
            
        return {
            "status": status,
            "timestamp": time.time(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
                "storage": storage_info
            },
            "service": {
                "name": config.service_name,
                "version": config.service_version,
                "environment": config.environment
            },
            "monitoring": {
                "sentry_enabled": config.enable_sentry,
                "tracing_enabled": config.enable_tracing,
                "metrics_enabled": config.enable_metrics
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e)
        }


@asynccontextmanager
async def setup_monitoring():
    """Context manager for monitoring setup and cleanup"""
    setup_logging()
    setup_sentry()
    setup_opentelemetry()
    setup_auto_instrumentation()
    
    logger = structlog.get_logger("gumstamp.monitoring")
    logger.info(
        "Monitoring initialized",
        service_name=config.service_name,
        version=config.service_version,
        environment=config.environment,
        sentry_enabled=config.enable_sentry,
        tracing_enabled=config.enable_tracing,
        metrics_enabled=config.enable_metrics
    )
    
    yield
    
    logger.info("Monitoring shutdown")


# Export for easy importing
__all__ = [
    "MonitoringConfig",
    "MonitoringMiddleware", 
    "BusinessMetrics",
    "SystemMetrics",
    "get_health_status",
    "setup_monitoring",
    "config"
]