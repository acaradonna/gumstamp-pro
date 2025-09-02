# Gumstamp Alerting & Incident Response Guide

## Alert Configuration

### Critical Alerts (Immediate Response Required)

#### 1. Service Down
- **Trigger**: `/healthz` endpoint fails 2 consecutive times
- **Monitor**: Better Uptime HTTP check
- **Response Time**: < 5 minutes
- **Actions**:
  1. Check Render service status
  2. Review application logs for errors
  3. Restart service if needed
  4. Escalate if restart doesn't resolve

#### 2. High Error Rate
- **Trigger**: >5% HTTP 5xx responses over 5 minutes
- **Monitor**: Sentry + Grafana alert
- **Response Time**: < 15 minutes
- **Actions**:
  1. Check Sentry for error details
  2. Review system resources (CPU, memory)
  3. Check for recent deployments
  4. Rollback if caused by recent release

#### 3. Storage Full
- **Trigger**: >90% disk usage
- **Monitor**: Custom metrics alert
- **Response Time**: < 30 minutes
- **Actions**:
  1. Check disk usage: `GET /health`
  2. Clean up old stamped files if safe
  3. Increase storage capacity in Render
  4. Implement automatic cleanup if needed

### Warning Alerts (Monitor & Plan)

#### 4. Slow Response Times
- **Trigger**: >2s average response time over 10 minutes
- **Monitor**: Grafana alert on request duration
- **Response Time**: < 1 hour
- **Actions**:
  1. Check system resource usage
  2. Identify slow endpoints in traces
  3. Optimize PDF processing if needed
  4. Consider scaling up resources

#### 5. High Resource Usage
- **Trigger**: >80% CPU or Memory for >15 minutes
- **Monitor**: System metrics alert
- **Response Time**: < 2 hours
- **Actions**:
  1. Check for resource-intensive operations
  2. Review concurrent user load
  3. Consider vertical scaling
  4. Optimize resource usage

#### 6. Upload Failures
- **Trigger**: >10% upload failures over 1 hour
- **Monitor**: Business metrics alert
- **Response Time**: < 4 hours
- **Actions**:
  1. Check file validation errors
  2. Review PDF processing issues
  3. Check storage write permissions
  4. Validate file size limits

## Alert Setup Instructions

### Better Uptime Configuration

1. **Uptime Monitor**:
   ```
   URL: https://your-app.onrender.com/healthz
   Check interval: 3 minutes
   Timeout: 30 seconds
   ```

2. **Performance Monitor**:
   ```
   URL: https://your-app.onrender.com/health
   Check interval: 5 minutes
   Response time threshold: 5 seconds
   ```

### Grafana Alerting

1. **High Error Rate Alert**:
   ```promql
   (
     rate(http_requests_total{status_code=~"5.."}[5m]) / 
     rate(http_requests_total[5m])
   ) * 100 > 5
   ```

2. **Slow Response Time Alert**:
   ```promql
   histogram_quantile(0.95, 
     rate(http_request_duration_seconds_bucket[10m])
   ) > 2
   ```

3. **Storage Usage Alert**:
   ```promql
   (
     gumstamp_storage_disk_bytes{type="used"} / 
     (gumstamp_storage_disk_bytes{type="used"} + gumstamp_storage_disk_bytes{type="free"})
   ) * 100 > 80
   ```

### Sentry Alerting

1. **Error Rate Alert**:
   - Go to Alerts → Create Alert
   - Condition: Error count > 10 in 5 minutes
   - Environment: production

2. **Performance Alert**:
   - Alert type: Metric alert
   - Metric: Transaction duration (p95)
   - Threshold: > 2000ms over 10 minutes

## Incident Response Process

### 1. Detection
- Automated alerts (email, Slack, PagerDuty)
- Manual discovery through monitoring dashboards
- User reports or complaints

### 2. Initial Response (0-15 minutes)
1. **Acknowledge** the alert to prevent spam
2. **Assess** severity and impact using monitoring dashboards
3. **Check** recent deployments or changes
4. **Gather** initial information from logs and metrics

### 3. Investigation (15-60 minutes)
1. **Deep dive** into Sentry errors and traces
2. **Analyze** system resources and performance metrics
3. **Check** external dependencies (Render status)
4. **Identify** root cause or likely culprits

### 4. Mitigation (As quickly as possible)
1. **Quick fixes**: Restart service, scale resources
2. **Rollback**: Revert recent deployments if applicable
3. **Workarounds**: Temporary solutions to restore service
4. **Resource scaling**: Increase CPU/memory if needed

### 5. Resolution & Recovery
1. **Implement** permanent fix
2. **Verify** solution resolves the issue
3. **Monitor** for stability over time
4. **Update** documentation and runbooks

### 6. Post-Incident (Within 24 hours)
1. **Document** timeline and actions taken
2. **Identify** root cause and contributing factors
3. **Plan** preventive measures
4. **Update** monitoring and alerting if needed

## Escalation Matrix

### Level 1: Automated Response
- Service restarts
- Auto-scaling (if configured)
- Circuit breaker patterns

### Level 2: On-Call Engineer
- Manual investigation and mitigation
- System administration tasks
- Quick fixes and workarounds

### Level 3: Senior Engineer/Architect  
- Complex system issues
- Architecture changes needed
- Major incident coordination

### Level 4: Business Leadership
- Customer-impacting outages >4 hours
- Security incidents
- Data loss scenarios

## Communication Templates

### Incident Status Update
```
🚨 INCIDENT UPDATE - [SEVERITY] - [TIMESTAMP]

Issue: [Brief description]
Impact: [What's affected and how many users]
Status: [Investigating/Mitigating/Resolved]
ETA: [Expected resolution time]

Next update: [When you'll provide next update]
```

### Resolution Notification
```
✅ RESOLVED - [TIMESTAMP]

The issue with [brief description] has been resolved.

Duration: [Total time]
Root cause: [Brief explanation]
Fix: [What was done]

We'll monitor closely and provide a detailed post-mortem within 24 hours.
```

## Monitoring Dashboard URLs

Keep these bookmarked for quick access:

- **Grafana Dashboard**: [Your Grafana Cloud URL]
- **Sentry Issues**: [Your Sentry project URL]  
- **Better Uptime Status**: [Your Better Uptime dashboard]
- **Render Metrics**: [Render dashboard for your service]

## Key Metrics for Investigation

### Performance Issues
1. Response time percentiles (p50, p95, p99)
2. Request rate and error rate
3. CPU and memory usage trends
4. Database/storage performance

### Error Investigation  
1. Error frequency and patterns
2. Stack traces and error context
3. User sessions affected
4. Geographic distribution of errors

### Capacity Planning
1. Resource utilization trends
2. Growth in traffic/usage
3. Storage usage patterns
4. Cost per transaction trends

## Prevention Strategies

### 1. Proactive Monitoring
- Set up trend analysis alerts
- Monitor capacity utilization  
- Track business metric anomalies
- Regular health check reviews

### 2. Automated Responses
- Auto-scaling based on load
- Circuit breakers for dependencies
- Automatic file cleanup policies
- Health-based load balancing

### 3. Regular Testing
- Load testing before major releases
- Disaster recovery drills
- Alert validation and testing
- Performance regression testing

### 4. Documentation
- Keep runbooks updated
- Document known issues and fixes
- Maintain troubleshooting guides
- Update monitoring as system evolves

## Common Issues & Solutions

### High CPU Usage
**Symptoms**: Slow response times, high system load
**Causes**: Large PDF processing, high traffic
**Solutions**: Scale vertically, optimize PDF operations, implement queuing

### Memory Leaks
**Symptoms**: Gradually increasing memory usage
**Causes**: PDF objects not being released, large file caching
**Solutions**: Review file handling, implement memory limits, restart service

### Disk Space Issues
**Symptoms**: Write failures, 500 errors
**Causes**: Too many stamped files, no cleanup policy
**Solutions**: Implement file cleanup, increase storage, monitor usage

### Network Connectivity
**Symptoms**: Timeout errors, external service failures
**Causes**: Network issues, third-party service problems
**Solutions**: Implement retries, check service status, use circuit breakers

Remember: The goal is to detect issues before they impact users and resolve them quickly when they do occur.