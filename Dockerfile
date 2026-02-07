# ---- Builder stage ----
FROM python:3.11-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies only (no dev group)
RUN uv sync --frozen --no-dev

# Copy source and config
COPY src/ src/
COPY config/ config/

# Install the project itself
RUN uv sync --frozen --no-dev

# ---- Runtime stage ----
FROM python:3.11-slim

# Install Playwright system dependencies + Chromium
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
        libcups2 libdrm2 libxkbcommon0 libatspi2.0-0 libxcomposite1 \
        libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
        libcairo2 libasound2 libwayland-client0 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual env and project from builder
COPY --from=builder /app/.venv .venv
COPY --from=builder /app/src src
COPY --from=builder /app/config config
COPY --from=builder /app/pyproject.toml .

# Install Playwright browsers (Chromium only)
RUN .venv/bin/python -m playwright install chromium

EXPOSE 9100

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9100/health')" || exit 1

ENV JARVIS_CONFIG=/app/config/jarvis-docker.yaml

CMD [".venv/bin/python", "-m", "jarvis"]
