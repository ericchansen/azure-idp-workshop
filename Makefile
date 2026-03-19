.PHONY: help lint format typecheck test test-e2e test-smoke test-all serve docker-build clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

lint: ## Run linter
	uv run ruff check .

format: ## Check formatting
	uv run ruff format --check .

typecheck: ## Run type checker
	uv run pyright

test: ## Run unit tests
	uv run pytest -v

test-e2e: ## Run structural E2E tests (mocked)
	npx playwright test --grep-invert Smoke --project="Desktop Edge"

test-smoke: ## Run smoke E2E tests (live, requires deployed app)
	node scripts/require-smoke-base-url.js && npx playwright test --grep Smoke --project="Desktop Edge"

test-all: lint format typecheck test test-e2e ## Run all checks and tests

serve: ## Start local dev server
	uv run uvicorn workshop.server:app --host 0.0.0.0 --port 8080 --reload

docker-build: ## Build Docker image locally
	docker build -t idp-workshop:local .

clean: ## Clean generated files
	rm -rf .pytest_cache .ruff_cache .coverage coverage.xml htmlcov playwright-report test-results __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
