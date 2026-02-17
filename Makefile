.PHONY: help install dev test lint format run docker-build docker-run clean

# Default target
help:
	@echo "OpenStack VM Lifecycle API - Development Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install       Install production dependencies"
	@echo "  dev           Install development dependencies"
	@echo "  run           Run the development server"
	@echo "  test          Run tests"
	@echo "  test-cov      Run tests with coverage"
	@echo "  lint          Run linting checks"
	@echo "  format        Format code with black"
	@echo "  type-check    Run mypy type checking"
	@echo "  docker-build  Build Docker image"
	@echo "  docker-run    Run with Docker Compose"
	@echo "  docker-stop   Stop Docker containers"
	@echo "  clean         Clean up generated files"
	@echo ""

# Install production dependencies
install:
	pip install --upgrade pip
	pip install -r requirements.txt

# Install development dependencies
dev:
	pip install --upgrade pip
	pip install -e ".[dev]"

# Run the development server
run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
test-cov:
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

# Run linting checks
lint:
	ruff check app/ tests/
	black --check app/ tests/

# Format code
format:
	black app/ tests/
	ruff check --fix app/ tests/

# Run type checking
type-check:
	mypy app/ --ignore-missing-imports

# Build Docker image
docker-build:
	docker build -t openstack-vm-api:latest .

# Run with Docker Compose
docker-run:
	docker-compose up -d

# Stop Docker containers
docker-stop:
	docker-compose down

# View Docker logs
docker-logs:
	docker-compose logs -f

# Clean up generated files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -f openstack_vm.db 2>/dev/null || true

# Initialize database
init-db:
	python -c "import asyncio; from app.database import create_tables; asyncio.run(create_tables())"

# Generate API key
gen-api-key:
	python -c "import secrets; print(f'API_KEY={secrets.token_urlsafe(32)}')"
