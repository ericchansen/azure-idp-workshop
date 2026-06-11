# Azure IDP Workshop

Interactive zero-to-hero workshop comparing **Azure Document Intelligence (DI)** and **Azure Content Understanding (CU)**.

## What This Is

A web-based training tool with progressive modules that teach you:
1. **Module 1 — Structured Extraction**: When DI wins. Forms with predefined fields — DI excels at confidence scoring, cost, and determinism.
2. **Module 2 — Unstructured Documents**: When DI falls short. CU infers semantic meaning from contracts and complex documents.
3. **Module 3 — Custom & Inferred Fields**: CU's unique power. GenAI-driven extraction without predefined fields or training.
4. **Decision Guide**: Interactive decision tree and comparison matrix to pick the right service.

Every operation shows the **actual API request and response** — no black boxes.

Bundled samples are provided for guided demos, and each module also supports uploading your own document. Uploads are limited to 10 MB per file. Analysis-only uploads are request-scoped and are not stored by the app; search and batch workflows index extracted content and metadata into Azure AI Search.

## Key Insight

> Microsoft recommends **starting with Content Understanding** for most new document processing scenarios.
> CU builds on DI with GenAI-powered extraction, multimodal support, and improved accuracy.

## Quick Start

```bash
# Clone and install
git clone https://github.com/ericchansen/azure-idp-workshop.git
cd azure-idp-workshop
uv sync

# Configure Azure credentials
cp .env.template .env
# Edit .env with your AI Services endpoint and key

# Run locally
uv run uvicorn workshop.server:app --reload --port 8080
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.12 + FastAPI |
| Frontend | Jinja2 + Alpine.js + Tailwind CSS (CDN) |
| Azure SDKs | `azure-ai-documentintelligence`, `azure-ai-contentunderstanding` |
| Infra | Bicep → Azure Container Apps |
| CI/CD | GitHub Actions (OIDC) |

## Development

```bash
uv sync                          # Install dependencies
uv run ruff check .              # Lint
uv run ruff format --check .     # Format check
uv run pyright                   # Type check
uv run pytest -v                 # Test
docker build -t idp-workshop .   # Build container
```

### E2E test targets

- Structural E2E runs locally: `npx playwright test --grep-invert Smoke --project="Desktop Edge"`
- Smoke E2E must target a deployed app: `BASE_URL=https://your-app.azurecontainerapps.io npx playwright test --grep Smoke --project="Desktop Edge"`
- The smoke suite now fails fast if `BASE_URL` is missing or points at `localhost`, so local Azure config issues do not masquerade as deployment regressions.

### Container image compliance

- Base image updates are tracked by Dependabot (`docker` ecosystem, weekly cadence).
- CI blocks fixable `CRITICAL/HIGH` container vulnerabilities via Trivy before merge.
- Production and preview deploy workflows re-scan built images before push to ACR.
- Trivy JSON scan artifacts are retained in CI for triage/auditing.

### Canonical health endpoints

- Public health endpoint: `GET /api/health`
- Deep configuration check: `GET /api/health?deep=true`
- CI, deploy health checks, smoke tests, and Container App probes all target `/api/health`.

## Architecture

```
User Browser
    │
    ▼
FastAPI (Jinja2 + Alpine.js)
    │
    ├─► Azure Document Intelligence (DI)
    ├─► Azure Content Understanding (CU)
    └─► Azure AI Search (indexed extracted content)
```

For detailed technical architecture, deployment patterns, and design decisions, see [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md).

## Repository Settings

### Branch Protection (Recommended)

To maintain code quality and prevent accidental breaking changes, configure the following branch protection rules on the main branch via GitHub UI:

- **Require status checks to pass before merging**:
  - `CI / Lint & Test`
  - `CI / Docker Build & Scan`
  - `CI / E2E Structural Tests`
- **Require at least 1 pull request review** before merging
- **Require branches to be up to date before merging**
- **Do not allow bypassing** these settings (enforce for administrators)

## License

MIT
