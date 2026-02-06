.PHONY: test test-all test-int lint typecheck docker-up docker-down run seed health

test:
	uv run pytest tests/unit/ -v

test-all:
	uv run pytest tests/ -v

test-int:
	uv run pytest tests/integration/ -v

lint:
	uv run ruff check src/ tests/

typecheck:
	uv run mypy src/jarvis/

docker-up:
	docker compose up -d

docker-down:
	docker compose down

run:
	uv run python -m jarvis

seed:
	uv run python scripts/seed_agent.py

health:
	uv run python scripts/healthcheck.py
