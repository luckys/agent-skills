# Observability

A reliable API is an observable API. Without logs, metrics, and request tracing, diagnosing production issues requires guesswork.

## Request IDs

Include a unique identifier in every response. Clients include it when reporting issues; your logging pipeline uses it to correlate all events for that request across services.

```
# Server generates and returns the ID
X-Request-ID: f47ac10b-58cc-4372-a567-0e02b2c3d479

# If the client sends one, echo it back — allows end-to-end tracing
X-Request-ID: client-provided-uuid
```

Rules:
- Generate a UUID v4 server-side if the client does not provide one.
- Propagate the request ID to all downstream service calls (pass it in internal request headers).
- Include it in every log line for the duration of the request.
- Never trust a client-provided ID for security purposes — only use it for correlation.

## What to Log

Log at the structured (JSON) level, not as unformatted strings. Every request log entry should include:

```json
{
  "requestId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "method": "POST",
  "path": "/v1/orders",
  "statusCode": 422,
  "durationMs": 34,
  "userId": "usr_01J8X",
  "userAgent": "MyApp/2.1 (iOS 17)",
  "ip": "203.0.113.5"
}
```

Never log:
- Request bodies that may contain passwords, tokens, or PII.
- Authorization header values.
- Full credit card numbers or payment data.
- Raw user-supplied strings without sanitization.

## Metrics to Track

| Metric | Why it matters |
|--------|---------------|
| Request rate (rpm) | Traffic baseline; spike detection |
| Error rate (4xx, 5xx %) | API health; regression detection |
| Latency (p50, p95, p99) | Performance SLO tracking |
| Endpoint-level breakdown | Identify slow or error-prone routes |
| Rate limit hit rate | Signal capacity or abuse issues |

Set alerts on error rate spikes (e.g., 5xx > 1% of requests) and latency degradation (p99 > threshold).

## Distributed Tracing

In microservice environments, propagate trace context using standard headers:

```
# W3C Trace Context (standard)
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01

# Or OpenTelemetry / Jaeger / Zipkin B3 headers
X-B3-TraceId: 4bf92f3577b34da6a3ce929d0e0e4736
X-B3-SpanId: 00f067aa0ba902b7
```

Propagating trace IDs lets you reconstruct the full call graph when a request touches multiple services.

## Health Endpoints

Expose at minimum two health endpoints — not versioned, never authenticated:

```
GET /health          → liveness: is the process running?
GET /health/ready    → readiness: is the service ready to receive traffic?
```

Liveness response (200 or 503):
```json
{ "status": "ok" }
```

Readiness response — include dependency checks:
```json
{
  "status": "ok",
  "checks": {
    "database": "ok",
    "redis":    "ok",
    "stripe":   "degraded"
  }
}
```

Return 503 Service Unavailable when the service is not ready. Load balancers and orchestrators (Kubernetes) use readiness to route traffic.

## Alerting Checklist

- 5xx rate > 1% sustained for 2 minutes → page on-call
- p99 latency > SLO threshold → page on-call
- Rate limit saturation > 80% → notify team
- Upstream dependency health check failing → notify team
- Zero requests in a window where traffic is expected → page on-call (dead man's switch)
