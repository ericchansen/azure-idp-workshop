# Azure IDP Workshop

Interactive zero-to-hero workshop comparing **Azure Document Intelligence (DI)** and **Azure Content Understanding (CU)**.

## What This Is

A web-based training tool with progressive modules that teach you:
1. **Module 1 — OCR & Layout**: How both services digitize documents
2. **Module 2 — Prebuilt Models**: Head-to-head comparison on invoices and receipts
3. **Module 3 — Custom Fields**: CU's GenAI-powered field inference (summaries, entities, sentiment)
4. **Decision Guide**: When to use DI vs CU, with interactive decision tree

Every operation shows the **actual API request and response** — no black boxes.

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
| Frontend | Jinja2 + HTMX + Alpine.js + Tailwind CSS (CDN) |
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

## Architecture

```
User Browser
    │
    ▼
FastAPI (Jinja2 + HTMX)
    │
    ├─► Azure Document Intelligence (DI)
    ├─► Azure Content Understanding (CU)
    └─► Azure Blob Storage (samples)
```

## License

MIT
