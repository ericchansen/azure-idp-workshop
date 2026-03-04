# Azure IDP Workshop — Architecture & Technical Reference

This document describes the technical architecture of the Azure IDP Workshop, a comprehensive interactive demo comparing **Azure Document Intelligence (DI)** and **Azure Content Understanding (CU)** for document processing.

> **For contributors**, see [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## Quick Navigation

1. [Authentication & Credentials](#authentication--credentials)
2. [Application Architecture](#application-architecture)
3. [Infrastructure (Bicep)](#infrastructure-bicep)
4. [CI/CD Pipelines](#cicd-pipelines)
5. [Testing Architecture](#testing-architecture)
6. [Environment Variables](#environment-variables)

---

## Authentication & Credentials

### Credential Resolution Strategy

The app implements a **dual-credential strategy**:

1. **Local Development**: Use API key from `.env` file via `AzureKeyCredential`
2. **Production**: Use managed identity via `DefaultAzureCredential` (no secrets stored)

```python
# src/workshop/config.py and services use this pattern:
if settings.ai_services_key:
    from azure.core.credentials import AzureKeyCredential
    credential = AzureKeyCredential(settings.ai_services_key)
else:
    from azure.identity import DefaultAzureCredential
    credential = DefaultAzureCredential()
```

### Production: Managed Identity

In Container Apps, the app runs under a **user-assigned managed identity** (`idp-id` or `idp-id-stage`):

- **Bicep creates** the identity resource
- **Azure CLI assigns** three RBAC roles (idempotent via `az role assignment create`):
  - `Storage Blob Data Contributor` — Read/write blob storage
  - `Cognitive Services User` — Access DI & CU APIs
  - `ACR Pull` — Pull container images

Env vars injected by Bicep:
- `AZURE_CLIENT_ID` — Identity client ID (tells `DefaultAzureCredential` which identity to use)
- `AI_SERVICES_ENDPOINT` — Azure AI Services endpoint
- `STORAGE_ACCOUNT_URL` — Blob storage endpoint

### CI/CD: OIDC Federation

GitHub Actions workflows authenticate via **OpenID Connect federation** (no service principal passwords):

```yaml
permissions:
  id-token: write
  contents: read

- name: Azure Login
  uses: azure/login@a457da9ea143d694b1b9c7c869ebb04ebe844ef5 # v2
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

GitHub generates a short-lived OIDC token; no long-lived secrets.

---

## Application Architecture

### Structure

```
src/workshop/
├── config.py                          # Pydantic Settings (env vars)
├── server.py                          # FastAPI app initialization
├── routers/
│   ├── di.py          (/api/di/*)     # Document Intelligence endpoints
│   ├── cu.py          (/api/cu/*)     # Content Understanding endpoints
│   ├── documents.py   (/api/documents/)  # Sample documents
│   └── health.py      (/api/health)   # Health check
├── services/
│   ├── document_intelligence.py       # DI SDK wrapper
│   ├── content_understanding.py       # CU SDK wrapper
│   └── api_trace.py                   # Request/response capture for UI
├── templates/
│   ├── base.html                      # Layout (Tailwind, Alpine.js)
│   ├── index.html                     # Landing page
│   ├── module1.html                   # Module 1: Structured Extraction
│   ├── module2.html                   # Module 2: Semantic Extraction
│   ├── module3.html                   # Module 3: Custom Fields
│   ├── guide.html                     # Decision Guide
│   └── partials/                      # Reusable fragments
└── static/
    ├── css/
    └── js/
```

### API Endpoints

#### Page Routes (Server-Side Rendering)
| Path | Purpose |
|------|---------|
| `GET /` | Landing page |
| `GET /module/1` | Structured Extraction demo |
| `GET /module/2` | Semantic Extraction demo |
| `GET /module/3` | Custom Fields demo |
| `GET /guide` | Decision Guide |

#### Document Intelligence API
| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/di/layout` | Analyze document layout |
| `POST` | `/api/di/prebuilt/{model}` | Prebuilt model analysis (invoice, receipt, etc.) |

#### Content Understanding API
| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/cu/layout` | CU layout analysis |
| `POST` | `/api/cu/prebuilt/{model}` | CU prebuilt analyzer |
| `POST` | `/api/cu/custom` | Custom field extraction |

#### Documents API
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/documents/samples` | List sample files |
| `GET` | `/api/documents/samples/{filename}/raw` | Serve raw file bytes |
| `POST` | `/api/documents/upload` | Upload document (10MB max) |

#### Health & Status
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/health` | Basic health check |
| `GET` | `/api/health?deep=true` | Deep check with service configuration |

### Frontend Tech Stack

| Technology | Role |
|-----------|------|
| **Jinja2** | Server-side template rendering |
| **Tailwind CSS** (CDN) | Styling |
| **Alpine.js** (CDN) | Client-side reactivity (forms, result display) |
| **Prism.js** (CDN) | JSON/Python/Bash syntax highlighting |
| **Marked.js** (CDN) | Markdown rendering (CU results) |

All frontend code is vanilla JavaScript — no build step, no SPA framework. Alpine.js provides lightweight reactivity for user interactions. Page navigation triggers full page reloads.

### Service Layer Patterns

Both DI and CU services follow consistent patterns:

1. **Lazy initialization** — SDK clients created on first call
2. **Async execution** — `asyncio.to_thread()` wraps blocking SDK calls
3. **Trace capture** — Every API call records request/response (headers redacted)
4. **Unified response** — Always returns `{"result": {...}, "trace": {...}}`
5. **Error handling** — Exceptions caught and recorded in trace, safe error returned to UI

---

## Infrastructure (Bicep)

### Resource Architecture

```
Resource Group: rg-idp-workshop
├── AI Services (idp-workshop-ai, kind: AIServices, SKU: S0)
│   ├── GPT-4.1 deployment
│   └── text-embedding-3-large deployment
├── Storage Account (idpworkshopstorage)
├── Log Analytics (idp-workshop-logs)
├── Container Registry (idpworkshopacr)
├── Managed Identity (idp-id / idp-id-stage)
├── Container App Environment (idp-cae / idp-cae-stage)
└── Container App (idp-workshop / idp-workshop-stage)
```

### Bicep Modules

| Module | File | Purpose |
|--------|------|---------|
| **main.bicep** | `infra/main.bicep` | Orchestration — creates all resources |
| **ai-services** | `infra/modules/ai-services.bicep` | AI Services + model deployments |
| **storage** | `infra/modules/storage.bicep` | Storage account with hardening |
| **log-analytics** | `infra/modules/log-analytics.bicep` | Logging and diagnostics |
| **acr** | `infra/modules/acr.bicep` | Container Registry |
| **container-app-env** | `infra/modules/container-app-env.bicep` | Container Apps Environment |
| **container-app** | `infra/modules/container-app.bicep` | Container App (conditional) |

### Environment-Specific Naming

Environment variables in `main.bicep` generate per-environment names:

| Resource | Prod | Stage |
|----------|------|-------|
| Container App Env | `idp-cae` | `idp-cae-stage` |
| Container App | `idp-workshop` | `idp-workshop-stage` |
| Managed Identity | `idp-id` | `idp-id-stage` |

**Shared across environments**: AI Services, Storage, Log Analytics, Container Registry.

### Container App Configuration

| Setting | Value |
|---------|-------|
| **CPU** | 0.5 cores |
| **Memory** | 1 Gi |
| **Min replicas** | 1 (prod) / 0 (stage) |
| **Max replicas** | 3 (prod) / 1 (stage) |
| **Auto-scaling rule** | 20 concurrent HTTP requests |
| **Revisions mode** | Multiple (for PR previews) |

---

## CI/CD Pipelines

### Workflow Overview

```
PUSH TO MAIN
    ↓
┌─────────────────────────────────┐
│  CI (ci.yml) — 3 parallel jobs  │
│  • Lint & test (pytest)         │
│  • Docker build & Trivy scan    │
│  • Structural E2E tests         │
└──────────┬──────────────────────┘
           ↓ (all pass)
┌──────────────────────────────────┐
│ Deploy Prod (deploy-prod.yml)    │
│ • Bicep infrastructure           │
│ • Role assignments (CLI)         │
│ • Build & push Docker image      │
│ • Deploy to Container Apps       │
└──────────┬──────────────────────┘
           ↓
┌──────────────────────────────────┐
│ Smoke Tests (live Azure APIs)    │
│ (continue-on-error: true)        │
└──────────────────────────────────┘
```

### CI Workflow

**Trigger**: Push to main, PR to main, manual dispatch

**Jobs** (3 parallel):

| Job | Steps | Purpose |
|-----|-------|---------|
| **Lint & Test** | ruff check → ruff format → pyright → pytest | Code quality, type safety, logic correctness |
| **Docker Build & Scan** | docker build → Trivy | Vulnerability scanning |
| **E2E Structural** | Start server → Playwright `--grep-invert Smoke` | UI structure, error handling, JS correctness (mocked) |

**Test must-passes**:
- pytest: ≥55% code coverage
- Trivy: No CRITICAL or unfixed HIGH vulnerabilities
- E2E: No console errors, all assertions pass

### Deploy Production Workflow

**Trigger**: CI success on main, or manual dispatch

**Steps**:

1. Azure Login (OIDC federation)
2. **Ensure infrastructure** — `az deployment group create` with `infra/main.bicep`
3. **Ensure role assignments** — 3x `az role assignment create` (idempotent, `|| true`)
4. **Re-authenticate** — Token may expire during Bicep deployment
5. **ACR Login** — Prepare for image push
6. **Build & Push** — Docker image tagged `sha-{7-char SHA}`
7. **Deploy app revision** — `az containerapp update --image`
8. **Route traffic** — `az containerapp ingress traffic set --revision-weight latest=100`
9. **Smoke Test** — Run Playwright against live deployed app (`continue-on-error: true`)

**Smoke Test Job**:
- Runs against **real deployed app** (no mocks)
- Uses `continue-on-error: true` so CU flakiness doesn't fail the deploy
- Uploads HTML report artifact (14-day retention)

### Pull Request Staging Workflow

**Trigger**: PR opened, synchronized, reopened, closed

**Architecture**: Azure Container Apps **multi-revision mode** with zero-traffic labeled revisions for PR previews.

**Key steps**:
1. Enable multi-revision mode
2. Build & push image tagged `pr-{N}-{SHA}`
3. Deploy as zero-traffic revision
4. Run E2E structural tests
5. Comment PR with preview URL
6. On PR close: Deactivate revision (automatic cleanup)

---

## Testing Architecture

### 3-Tier Pyramid

```
               /\
              /  \  Smoke E2E (live Azure APIs)
             /    \
            /──────\
           /        \
          / Structural E2E (mocked, fast)
         /──────────────\
        /                \
       /    Unit Tests    \
      /──────────────────────\
```

### Test Layers

#### Unit Tests (`tests/test_*.py`)
- **Tool**: pytest
- **Mocked**: Everything (no API calls)
- **Coverage**: ≥55% required
- **Async mode**: auto (all tests run async)
- **Command**: `uv run pytest -v`

#### Structural E2E (`tests/e2e/*.spec.ts`)
- **Tool**: Playwright
- **Mocked**: All API responses (intercepted at HTTP level)
- **Purpose**: UI structure, error handling, JavaScript correctness
- **Speed**: ~2-3 minutes total
- **Command**: `npx playwright test --grep-invert Smoke --project="Desktop Edge"`

#### Smoke E2E (`tests/e2e/smoke.spec.ts`)
- **Tool**: Playwright
- **Mocked**: None (real Azure APIs)
- **Purpose**: End-to-end validation of deployed app
- **Requirement**: Must pass before declaring work done
- **Command**: `BASE_URL=https://deployed-app npx playwright test --grep Smoke --project="Desktop Edge"`

### Console Error Detection

All E2E tests use a shared fixture that **automatically fails on unexpected console errors**:

```typescript
// tests/e2e/helpers.ts
export const consoleErrorHandler = test.extend({
  page: async ({ page }, use) => {
    page.on("console", (msg) => {
      // Whitelist expected messages (Vue Devtools, Alpine, etc.)
      // Fail test on unexpected errors
    });
    await use(page);
  },
});
```

### Test Configuration

**pytest** (`pyproject.toml`):
- Test dir: `tests/`
- Asyncio mode: auto
- Coverage: ≥55%, reporting: term + XML
- Markers: none (uses file naming convention)

**Playwright** (`playwright.config.ts`):
- Test dir: `tests/e2e/`
- Timeout: 3 minutes per test
- Expect timeout: 10 seconds
- Parallel: all tests in parallel
- Retries: 1 on failure
- Reporter: HTML
- Browser: Edge (msedge channel)

---

## Environment Variables

### Application Runtime

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AI_SERVICES_ENDPOINT` | Yes | `""` | Azure AI Services endpoint URL |
| `AI_SERVICES_KEY` | No | `""` | API key (if empty, uses managed identity) |
| `STORAGE_ACCOUNT_URL` | No | `""` | Azure Blob Storage endpoint |
| `AZURE_CLIENT_ID` | Yes (prod) | — | Managed identity client ID |
| `ENVIRONMENT` | No | `"dev"` | Environment (dev/stage/prod) |
| `LOG_LEVEL` | No | `"INFO"` | Python log level (DEBUG/INFO/WARNING/ERROR) |
| `CU_COMPLETION_DEPLOYMENT` | No | `"gpt-4.1"` | CU GPT-4 deployment name |
| `CU_EMBEDDING_DEPLOYMENT` | No | `"text-embedding-3-large"` | CU embedding deployment name |

### Loading

**Local development** (`.env` file):
```bash
AI_SERVICES_ENDPOINT=https://your-instance.openai.azure.com/
AI_SERVICES_KEY=your-key-here
STORAGE_ACCOUNT_URL=https://youraccount.blob.core.windows.net/
```

**Production** (via Bicep):
```bash
AI_SERVICES_ENDPOINT=<output from Bicep>
AZURE_CLIENT_ID=<output from Bicep>
STORAGE_ACCOUNT_URL=<output from Bicep>
ENVIRONMENT=prod
LOG_LEVEL=INFO
```

Settings loaded via Pydantic in `src/workshop/config.py`:

```python
class Settings(BaseSettings):
    ai_services_endpoint: str
    ai_services_key: str = ""
    storage_account_url: str = ""
    azure_client_id: str = ""
    environment: str = "dev"
    log_level: str = "INFO"
    cu_completion_deployment: str = "gpt-4.1"
    cu_embedding_deployment: str = "text-embedding-3-large"

    class Config:
        env_file = ".env"  # Load from .env in dev
```

---

## Key Design Decisions

### Why managed identity in production?

- **No secrets in code or environment**: Credentials managed by Azure
- **Automatic token refresh**: Azure SDK handles token lifecycle
- **Auditable**: All API calls logged to Azure Monitor via managed identity
- **Scoped permissions**: RBAC roles limit blast radius of a compromise

### Why role assignments via CLI instead of Bicep?

ARM's Bicep `roleAssignment` resource uses `@2022-04-01` API, which rejects re-PUTs of existing assignments with different generated names (`guid()`). The Azure CLI's `az role assignment create` is idempotent by principal + role + scope, avoiding conflicts.

### Why multi-revision Container Apps for staging?

- **Cost-efficient**: PR revisions share resources; no separate staging infrastructure
- **Label-based routing**: Each PR gets a unique preview URL (`https://app---pr-42.azurecontainerapps.io`)
- **Automatic cleanup**: PR close triggers revision deactivation
- **Production isolation**: Multi-revision mode doesn't affect production traffic routing

### Why separate test layers (unit, structural, smoke)?

- **Unit tests**: Fast feedback (25s), run on every commit
- **Structural E2E**: UI correctness without external dependencies (2-3 min), gates merges
- **Smoke E2E**: Real integration test, catches config errors in live deployment, requires human judgment to ignore transient failures

---

## Troubleshooting

### "Analysis Failed — Internal Server Error"
- **Cause**: Azure AI Services endpoint misconfigured or credentials expired
- **Fix**: Check `AI_SERVICES_ENDPOINT`, verify managed identity has `Cognitive Services User` role

### "Unexpected token" errors in browser
- **Cause**: Backend exception not caught, returning HTML error page instead of JSON
- **Fix**: Check application logs, ensure exception handling in all API routes

### Console JavaScript errors during E2E tests
- **Cause**: Alpine.js crash from unexpected API response shape
- **Fix**: Verify API response matches expected structure (see `services/*.py`)

### Smoke test failures after deployment
- **Cause**: Real Azure API issues (CU analyzer misconfigured, token expired)
- **Fix**: Check deployed app logs via Azure Portal > Container Apps > Revisions > Logs

---

## Further Reading

- [Azure Document Intelligence docs](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/)
- [Azure Content Understanding docs](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/)
- [Azure Container Apps docs](https://learn.microsoft.com/en-us/azure/container-apps/)
- [FastAPI docs](https://fastapi.tiangolo.com/)
- [Bicep docs](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
