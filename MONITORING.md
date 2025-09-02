# Gumstamp Monitoring & Observability Setup

This document provides a comprehensive guide for setting up monitoring and observability for the Gumstamp application deployed on Render.

## Overview

The monitoring stack includes:

- **OpenTelemetry**: Distributed tracing and metrics
- **Sentry**: Error tracking and performance monitoring  
- **Grafana Cloud**: Metrics visualization and alerting
- **Better Uptime**: External uptime monitoring
- **Structured Logging**: JSON-formatted logs for better parsing

## Quick Setup Guide

### 1. Sentry Setup (Error Tracking)

1. Sign up at [sentry.io](https://sentry.io)
2. Create a new Python project
3. Copy the DSN from Settings → Client Keys (DSN)
4. Add to Render environment variables:

   ```bash
   SENTRY_DSN=https://your-key@sentry.io/project-id
   ```

**Free Tier**: 5,000 errors/month, 10,000 performance units/month

### 2. Grafana Cloud Setup (Metrics & Dashboards)

1. Sign up at [grafana.com](https://grafana.com/auth/sign-up/create-account)
2. Go to "My Account" → "Security" → "Access Policies"
3. Create access policy with `metrics:write` and `logs:write` scopes
4. Create a token for the access policy
5. Find your OTLP endpoint in the Grafana Cloud portal
6. Add to Render environment variables (Grafana Cloud usually expects a Basic auth header constructed as "username:token" then base64-encoded; we pass it via GRAFANA_CLOUD_API_KEY and set the Authorization header automatically):

   ```bash
   OTLP_ENDPOINT=https://otlp-gateway-prod-us-east-0.grafana.net/otlp
   # Set to BASE64(username:token) only; code will prefix with "Basic "
   GRAFANA_CLOUD_API_KEY=$(printf 'username:token' | base64 -w0)
   ```

**Free Tier**: 10,000 active series, 50GB logs, 50GB traces

### 3. Better Uptime Setup (External Monitoring)

1. Sign up at [betteruptime.com](https://betteruptime.com)
2. Create HTTP monitors for:
   - `https://your-app.onrender.com/healthz` (simple health check)
   - `https://your-app.onrender.com/health` (detailed health status)
3. Set up alert channels (email, Slack, etc.)

**Free Tier**: 10 monitors, 3-minute intervals

### 4. Configure Render Environment Variables

In your Render dashboard, add these environment variables:

**Required**:

```bash
SENTRY_DSN=https://your-key@sentry.io/project-id
OTLP_ENDPOINT=https://otlp-gateway-prod-us-east-0.grafana.net/otlp
# BASE64(username:token); app will add the "Basic " prefix
GRAFANA_CLOUD_API_KEY=base64(username:token)
```

**Optional** (have sensible defaults):

```bash
ENVIRONMENT=production
ENABLE_TRACING=true
ENABLE_METRICS=true
SLOW_REQUEST_THRESHOLD=2.0
ERROR_RATE_THRESHOLD=5.0
```

## Available Endpoints

### Health Check Endpoints

- `GET /healthz` - Simple health check for load balancers
- `GET /health` - Comprehensive health status with system metrics
- `GET /metrics/business` - Business-specific metrics

Example `/health` response:

```json
{
  "status": "healthy",
  "timestamp": 1635724800.0,
  "system": {
    "cpu_percent": 25.4,
    "memory_percent": 67.2,
    "memory_available": 1073741824,
    "storage": {
      "total": 5368709120,
      "used": 1073741824,
      "free": 4294967296,
      "percent": 20.0
    }
  },
  "service": {
    "name": "gumstamp",
    "version": "abc123",
    "environment": "production"
  },
  "monitoring": {
    "sentry_enabled": true,
    "tracing_enabled": true,
    "metrics_enabled": true
  }
}
```

## Key Metrics Being Tracked

### Business Metrics

1. **PDF Operations**:
   - `gumstamp_pdf_operations_total` - Counter of PDF operations (upload, stamp)
   - `gumstamp_pdf_processing_seconds` - Processing time histogram
   - `gumstamp_upload_file_size_bytes` - Upload file size distribution

2. **Downloads**:
   - `gumstamp_downloads_total` - Successful/failed downloads
   - Download completion rates

3. **Token Operations**:
   - `gumstamp_token_operations_total` - Token creation and verification

### System Metrics

1. **Resource Usage**:
   - `gumstamp_system_cpu_percent` - CPU usage
   - `gumstamp_system_memory_bytes` - Memory usage
   - `gumstamp_storage_disk_bytes` - Disk usage

2. **Performance**:
   - HTTP request duration and status codes
   - Error rates and patterns

## Alerting Strategy

### Critical Alerts (Immediate Response)

1. **Service Down**: HTTP health check fails
   - Monitor: `/healthz` endpoint
   - Threshold: 2 consecutive failures
   - Response: Immediate investigation

2. **High Error Rate**: >5% of requests failing
   - Metric: HTTP 5xx responses / total requests
   - Threshold: 5% over 5-minute window
   - Response: Check logs and system resources

3. **Storage Full**: >90% disk usage
   - Metric: `gumstamp_storage_disk_bytes`
   - Threshold: 90% of total capacity
   - Response: Clear old files or increase storage

### Warning Alerts (Monitor Closely)

1. **Slow Response Times**: >2s average response time
   - Metric: HTTP request duration
   - Threshold: 2s average over 10 minutes
   - Response: Check for performance bottlenecks

2. **High Memory Usage**: >80% memory utilization  
   - Metric: `gumstamp_system_memory_bytes`
   - Threshold: 80% of available memory
   - Response: Monitor for memory leaks

3. **Upload Failures**: >10% PDF upload failures
   - Metric: `gumstamp_pdf_operations_total{success="false"}`
   - Threshold: 10% failure rate over 1 hour
   - Response: Check file validation and processing

## Grafana Dashboard Queries

### Key Performance Indicators

**Request Rate**:

```promql
rate(http_requests_total[5m])
```

**Error Rate**:

```promql
rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m])
```

**Response Time (95th percentile)**:

```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**PDF Processing Time**:

```promql
histogram_quantile(0.95, rate(gumstamp_pdf_processing_seconds_bucket[5m]))
```

### Business Metrics Queries

**Daily Downloads**:

```promql
increase(gumstamp_downloads_total{success="true"}[1d])
```

**Upload Success Rate**:

```promql
rate(gumstamp_pdf_operations_total{operation="upload",success="true"}[1h]) / rate(gumstamp_pdf_operations_total{operation="upload"}[1h])
```

**Storage Usage Trend**:

```promql
gumstamp_storage_disk_bytes{type="used"} / (gumstamp_storage_disk_bytes{type="used"} + gumstamp_storage_disk_bytes{type="free"})
```

## Cost Analysis

### Free Tier Limits (Monthly)

- **Sentry**: 5K errors, 10K performance units
- **Grafana Cloud**: 10K metrics series, 50GB logs
- **Better Uptime**: 10 monitors at 3-min intervals
- **Render**: Standard metrics included

**Estimated Cost**: $0/month for bootstrap stage

### Scaling Considerations

When you exceed free tiers:

- **Sentry Team**: $26/month for 50K errors
- **Grafana Cloud Pro**: $49/month for 100K series
- **Better Uptime Pro**: $18/month for 50 monitors

## Troubleshooting

### Common Issues

1. **Metrics Not Appearing in Grafana**:
   - Check OTLP_ENDPOINT and GRAFANA_CLOUD_API_KEY
   - Verify base64 encoding of API key
   - Check Render logs for connection errors

2. **Sentry Not Receiving Errors**:
   - Verify SENTRY_DSN format
   - Check that errors are actually occurring
   - Review Sentry project settings

3. **High Memory Usage**:
   - Monitor PDF file sizes being processed
   - Check for memory leaks in long-running processes
   - Consider implementing file size limits

### Log Analysis

Structured logs are output in JSON format. Key log events:

- `"event": "Request processed"` - HTTP request completion
- `"event": "PDF uploaded successfully"` - Successful uploads  
- `"event": "Download successful"` - File downloads
- `"event": "Slow request detected"` - Performance issues

## Security Considerations

1. **Sensitive Data**: Monitoring configuration excludes PII
2. **Token Data**: Tokens are not logged in plaintext  
3. **Error Handling**: Stack traces exclude sensitive environment data
4. **Access Control**: Monitoring endpoints don't expose sensitive information

## Maintenance

### Monthly Tasks

1. Review alert thresholds and adjust based on traffic patterns
2. Check free tier usage and plan for scaling
3. Analyze performance trends and optimization opportunities
4. Update monitoring configuration as application evolves

### Incident Response Process

1. **Detection**: Automated alerts or manual discovery
2. **Assessment**: Check `/health` endpoint and dashboard
3. **Mitigation**: Scale resources, restart services, or rollback
4. **Investigation**: Analyze traces, logs, and metrics
5. **Documentation**: Update runbooks and monitoring based on learnings

## Advanced Features

### Custom Dashboards

Create dashboards for:

- Executive summary (uptime, user activity, revenue impact)
- Engineering view (performance, errors, resource usage)  
- Business intelligence (usage patterns, popular features)

### Log-Based Alerting

Set up alerts based on log patterns:

- Consecutive authentication failures
- Unusual error message patterns
- Performance degradation indicators

### Infrastructure Monitoring

Monitor Render-specific metrics:

- Container restarts and crashes
- Network latency and bandwidth
- Deployment success/failure rates

## Getting Help

- **Sentry Documentation**: <https://docs.sentry.io/>
- **Grafana Cloud Docs**: <https://grafana.com/docs/grafana-cloud/>
- **OpenTelemetry Guides**: <https://opentelemetry.io/docs/>
- **Render Support**: <https://render.com/docs>

For Gumstamp-specific monitoring questions, check the application logs and health endpoints first, then refer to this documentation.
