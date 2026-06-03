.PHONY: install install-dev test lint format clean run-demo run-api help

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt
	pip install -e .

install-dev: ## Install development dependencies
	pip install -r requirements-dev.txt
	pip install -e ".[dev]"

test: ## Run test suite
	pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage report
	pytest tests/ --cov=explainer_factory --cov-report=term-missing --cov-report=html

lint: ## Run linter
	ruff check src/ tests/

format: ## Format code
	ruff format src/ tests/

typecheck: ## Run type checker
	mypy src/

clean: ## Clean temporary and build files
	rm -rf __pycache__ .pytest_cache .mypy_cache htmlcov .coverage
	rm -rf dist build *.egg-info
	rm -rf tmp/ outputs/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

run-demo: ## Run the demo pipeline
	python scripts/run_demo.py --topic "Quantum Entanglement"

run-api: ## Start the API server
	uvicorn explainer_factory.api.app:app --host 0.0.0.0 --port 8000 --reload

check: lint typecheck test ## Run all checks
