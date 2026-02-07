# Phase 8 Retro: Docker + Monitoring

## What was delivered

Two workstreams — monitoring infrastructure first (needed by Docker health checks), then Docker containerization.

### Monitoring
- **MonitoringSettings**: `metrics_enabled`, `log_format` in YAML config
- **Configurable structlog**: Console (dev) or JSON (Docker) renderer via `setup_logging(log_format=...)`
- **Prometheus metrics**: 5 metric objects — HTTP request counter/histogram, tool invocations, messages, errors
- **Enhanced `/health`**: Checks Letta connectivity, reports uptime/tool_count/channels, returns 503 when unhealthy
- **`/metrics`**: Prometheus text format endpoint (conditionally registered)
- **aiohttp middleware**: Request logging, metric updates, uncaught exception → 500 JSON with request_id
- **Message counters**: Inbound/outbound per channel in router

### Docker
- **Dockerfile**: Multi-stage (python:3.11-slim builder + runtime with Playwright Chromium)
- **docker-compose.yml**: 4 services (letta_db, letta_server, jarvis, whatsapp_bridge) with health checks
- **`jarvis-docker.yaml`**: Docker-specific config with service discovery hostnames, JSON logging
- **`.dockerignore`**: Excludes tests, docs, secrets, .git
- **Makefile**: `docker-build`, `docker-logs` targets

**Totals**: 30 tools, 28 HTTP endpoints, 202 tests (186 unit + 16 integration).

## Files created (10)

- `src/jarvis/monitoring/__init__.py`
- `src/jarvis/monitoring/metrics.py`
- `src/jarvis/monitoring/health.py`
- `src/jarvis/monitoring/middleware.py`
- `config/jarvis-docker.yaml`
- `Dockerfile`
- `.dockerignore`
- `tests/unit/test_monitoring_settings.py`
- `tests/unit/test_metrics.py`
- `tests/unit/test_health.py`
- `tests/unit/test_middleware.py`
- `tests/unit/test_docker_config.py`

## Files modified (11)

- `src/jarvis/settings.py` — added `MonitoringSettings`
- `src/jarvis/utils/logging.py` — configurable renderer (console/JSON)
- `src/jarvis/__main__.py` — pass `log_format` from settings
- `src/jarvis/http_server.py` — enhanced health, /metrics, middleware, new constructor params
- `src/jarvis/app.py` — pass new params, `mark_started()`, unpack `(agent, tool_count)`
- `src/jarvis/agent/factory.py` — returns `(agent, tool_count)` tuple
- `src/jarvis/channels/router.py` — MESSAGE_COUNT inbound/outbound increments
- `docker-compose.yml` — added jarvis service, health checks, fixed whatsapp bridge networking
- `Makefile` — added docker-build, docker-logs
- `config/jarvis.yaml` — added monitoring section
- `.env.example` — added Docker comment
- `pyproject.toml` — added prometheus-client
- `tests/unit/test_http_server.py` — enhanced health tests, /metrics tests
- `tests/unit/test_factory.py` — updated for tuple return
- `tests/unit/test_router.py` — added TestMessageCounters

## What went well

- Monitoring-first ordering was correct: the enhanced `/health` endpoint was needed for Docker health checks, and JSON logging was needed for container log aggregation.
- aiohttp middleware pattern cleanly separates observability concerns from endpoint handlers.
- TDD caught the `content_type` charset bug immediately — aiohttp rejects `text/plain; charset=utf-8` in the `content_type` parameter, requiring `headers=` instead.
- Delta-based Prometheus counter assertions (read before, act, read after) worked cleanly despite shared global registry.

## What could be better

- aiohttp middleware catching `web.HTTPException` (including 404) and wrapping as 500 was a subtle bug. The fix — `except web.HTTPException: raise` before `except Exception` — is simple but easy to miss.
- The `get_or_create_agent` return type change broke 2 existing factory tests. Predictable from the plan but still required test updates. If more callers existed, this would be higher risk.
- Prometheus Histogram `_sum` access uses `.get()` not `._value()` — the internal API between Counter and Histogram is inconsistent. Had to discover this at runtime.

## Docker validation (deferred)

Docker build and compose-up are not validated in this session — requires running Docker Desktop and having the Letta server image pulled. The Dockerfile and docker-compose.yml follow proven patterns from the existing WhatsApp bridge setup.

### To validate later:
- [ ] `docker compose build jarvis` succeeds
- [ ] `docker compose up -d` starts all 4 services
- [ ] `curl localhost:9100/health` returns ok with Letta check
- [ ] `curl localhost:9100/metrics` returns Prometheus format
- [ ] WhatsApp bridge reaches Jarvis at `http://jarvis:9100`
