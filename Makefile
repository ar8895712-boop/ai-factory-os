# ==============================================================
# Makefile — AI Factory Operating System Automation Toolkit
# Works on Linux, macOS, and Windows (via Git Bash / WSL / Make)
# ==============================================================

.PHONY: help setup test test-fast frontend-build docker-up docker-down clean seed

help:
	@echo "AI Factory Operating System — Available Commands:"
	@echo "  make setup            Set up Python venv, install deps & seed database"
	@echo "  make test             Run full 79-test suite with pytest"
	@echo "  make seed             Initialize database and seed the 6 machines"
	@echo "  make run-backend      Start FastAPI server locally on port 8000"
	@echo "  make run-frontend     Start Vite React dev server on port 5173"
	@echo "  make frontend-build   Compile React production bundle"
	@echo "  make docker-up        Build and start all services via Docker Compose"
	@echo "  make docker-down      Stop all running Docker Compose services"
	@echo "  make clean            Remove __pycache__, build artifacts, and caches"

setup:
	python -m pip install --upgrade pip
	pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
	pip install -r requirements.txt
	python scripts/seed_db.py
	cd frontend && npm install

test:
	pytest tests/ -v

test-fast:
	pytest tests/ -q

seed:
	python scripts/seed_db.py

run-backend:
	uvicorn backend.main:app --reload --port 8000

run-frontend:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/dist .ruff_cache htmlcov .coverage
