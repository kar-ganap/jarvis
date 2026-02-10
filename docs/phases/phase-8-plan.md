# Phase 8 Plan: Docker + Monitoring

## Scope

### Monitoring
- MonitoringSettings (metrics_enabled, log_format)
- Configurable structlog renderer (console/JSON)
- Prometheus metrics: HTTP requests, tool invocations, messages, errors
- Enhanced /health with Letta connectivity check
- /metrics endpoint (Prometheus format)
- aiohttp observability middleware
- Message counter instrumentation in router

### Docker
- Multi-stage Dockerfile (python:3.11-slim + Playwright Chromium)
- .dockerignore
- jarvis-docker.yaml with Docker service names
- Updated docker-compose.yml: jarvis service, health checks
- Makefile targets: docker-build, docker-logs

## Sub-phases

1. **8A**: MonitoringSettings + configurable logging + Prometheus metrics module
2. **8B**: Enhanced /health + HTTP middleware + /metrics endpoint + message counters
3. **8C**: Dockerfile + .dockerignore + docker-compose + Docker config YAML

## Test target

~34 new tests → ~202 total (186 unit + 16 integration)
