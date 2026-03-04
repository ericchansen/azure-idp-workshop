# Contributing to Azure IDP Workshop

## Getting Started

### Prerequisites

- **Python 3.12** — [Download](https://www.python.org/downloads/)
- **uv** — Python package manager. Install via: `pip install uv` or [See uv docs](https://docs.astral.sh/uv/getting-started/installation/)
- **Node.js 20+** — [Download](https://nodejs.org/)
- **Playwright** — Installed during setup (see below)

### Development Setup

```bash
# Install Python and Node.js dependencies
uv sync
npm ci

# Install Playwright browsers (required for E2E tests)
npx playwright install --with-deps msedge
```

## Running the App

```bash
# Start the FastAPI server on localhost:8000
uv run python -m workshop
```

Then open http://localhost:8000 in your browser.

## Testing

### Unit Tests
```bash
uv run pytest -v
```

Covers Python logic, API endpoints, and service layer. Requires **≥55% code coverage** to pass.

### Linting & Type Checking
```bash
uv run ruff check .              # Lint
uv run ruff format --check .     # Format check
uv run pyright                   # Type checking
```

### Structural E2E Tests (Mocked)
These test UI structure, error handling, and JavaScript correctness against mocked API responses. Fast, reliable, run locally.

```bash
# Start server first
uv run python -m workshop &

# Run structural tests
npx playwright test --grep-invert Smoke --project="Desktop Edge"
```

### Smoke E2E Tests (Live)
These test against the **real deployed application** with real Azure APIs. Required before declaring work done.

```bash
# Requires deployed app running
BASE_URL=https://your-deployed-app.azurecontainerapps.io \
  npx playwright test --grep Smoke --project="Desktop Edge"
```

## Branch Strategy

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b <type>/<short-description>
   ```
   Examples: `feat/custom-fields`, `fix/layout-bug`, `docs/readme-update`

2. **Never push directly to `main`** — all changes go via PR.

3. **Types** (conventional commits):
   - `feat` — New feature
   - `fix` — Bug fix
   - `docs` — Documentation
   - `refactor` — Code restructuring
   - `chore` — Build, dependencies, config
   - `test` — Test improvements
   - `ci` — Workflow/CI changes
   - `perf` — Performance improvement

## PR Process

1. Open a PR against `main`.
2. Verify CI passes:
   - Linting & type checking
   - Unit tests (≥55% coverage)
   - Structural E2E tests
   - Docker build & Trivy scan
3. Await review.
4. **Rebase merge only** — no squash, no merge commits.

## Code Style

- **Python**: Enforced by [Ruff](https://docs.astral.sh/ruff/) — autoformat with `uv run ruff format .`
- **Type hints**: Required for all public functions (checked by pyright)
- **TypeScript (E2E)**: Run formatter via `npm run format` if available
- **Comments**: Only where logic is non-obvious; avoid over-commenting

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

Examples:
- `feat(module-1): Add confidence scoring to DI results`
- `fix(cu-service): Handle ContentEmpty errors from binary upload`
- `docs(readme): Update tech stack section`

## Environment Variables

The application reads configuration from environment variables via `src/workshop/config.py`:

```python
class Settings(BaseSettings):
    ai_services_endpoint: str           # Azure AI Services endpoint
    ai_services_key: str = ""           # API key (optional; uses managed identity if empty)
    storage_account_url: str = ""       # Azure Blob Storage endpoint
    azure_client_id: str = ""           # Managed identity client ID (prod only)
    environment: str = "dev"            # Environment name (dev, stage, prod)
    log_level: str = "INFO"             # Python log level
    cu_completion_deployment: str = "gpt-4.1"
    cu_embedding_deployment: str = "text-embedding-3-large"
```

For local development, create a `.env` file:
```bash
cp .env.template .env
# Edit .env with your Azure credentials
```

**Never commit `.env`** — it's in `.gitignore`.

## Architecture & More

For architectural details, deployment patterns, CI/CD pipelines, and troubleshooting, see [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md).
