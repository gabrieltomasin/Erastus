.PHONY: up down migrate dev dev-frontend dev-worker logs

# Infrastructure
up:
	docker compose up -d

down:
	docker compose down

# Database
migrate:
	cd backend && alembic upgrade head

migration:
	cd backend && alembic revision --autogenerate -m "$(msg)"

# Development
dev:
	@echo "Starting backend..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

dev-worker:
	cd backend && celery -A app.workers.celery_app worker --loglevel=info --concurrency=1

# Logs
logs:
	docker compose logs -f

# Setup
setup: up
	sleep 3
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install
	$(MAKE) migrate
	@echo "Setup complete! Run 'make dev' and 'make dev-frontend' in separate terminals."
