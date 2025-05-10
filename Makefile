.PHONY: help install test format lint clean docker-build docker-up docker-down db-init dev

# Default target when running just 'make'
help:
	@echo "Available commands:"
	@echo "install      - Install project dependencies using Poetry"
	@echo "test        - Run tests with pytest"
	@echo "format      - Format code using black"
	@echo "lint        - Run flake8 linter"
	@echo "clean       - Remove Python compiled files and caches"
	@echo "docker-build- Build Docker images"
	@echo "docker-up   - Start all Docker containers"
	@echo "docker-down - Stop all Docker containers"
	@echo "db-init     - Initialize the database"
	@echo "dev         - Start development server"

# Install dependencies
install:
	poetry install

# Run tests
test:
	poetry run pytest tests/ -v

# Format code
format:
	poetry run black src/ tests/

# Run linter
lint:
	poetry run flake8 src/ tests/

# Clean Python compiled files and caches
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".coverage" -delete

# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Database initialization
db-init:
	poetry run python -m src.trendscout.db.init_db

# Development server
dev:
	poetry run uvicorn src.trendscout.main:app --reload --host 0.0.0.0 --port 8000
