# Makefile for the pump_well Python project

.PHONY: help install test lint format clean

help:
	@echo "Available commands:"
	@echo "  make install           - Install dependencies"
	@echo "  make install-dev       - Install dev dependencies"
	@echo "  make test              - Run tests"
	@echo "  make lint              - Lint (ruff) and type-check (mypy)"
	@echo "  make format            - Auto-fix and format code (ruff)"
	@echo "  make clean             - Clean up build artifacts"
	@echo "  make build             - Build the project (using uv build)"

build:
	uv build

install:
	uv sync

install-dev:
	uv sync --extra dev

test:
	uv run --extra dev pytest -v --cov=src tests/

lint:
	uv run ruff check src tests
	uv run mypy src/dbd

format:
	uv run ruff check --fix src tests

clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -f glue_job.zip
