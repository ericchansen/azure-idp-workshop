# AGENTS.md — Azure IDP Workshop

## Project Overview

Interactive demo comparing **Azure Document Intelligence (DI)** and **Azure Content Understanding (CU)**. Built with FastAPI + Alpine.js + Tailwind CSS.

## Definition of Done

A task is **NOT done** until ALL of the following pass:

### 1. Python Linting & Unit Tests
```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest -v
```

### 2. Playwright Structural E2E Tests (mocked — fast)
```bash
npx playwright test --grep-invert Smoke --project="Desktop Edge"
```
These use mocked API responses and validate UI structure, error handling, and JS correctness.

### 3. Playwright Smoke E2E Tests (live — MANDATORY before declaring done)
```bash
npx playwright test --grep Smoke --project="Desktop Edge"
```
These run against the **real deployed app** with **no mocks**. They catch:
- Misconfigured Azure endpoints
- Authentication failures
- Missing/broken API services
- Real "Internal Server Error" responses
- Console JS errors during actual usage

**If smoke tests fail, the demo is broken. Do not skip them.**

### 4. No Console Errors
All E2E tests use a shared console error detection fixture. Any unexpected `console.error` or page error fails the test automatically.

## Test Architecture

| Layer | File(s) | Mocked? | What it catches |
|-------|---------|---------|-----------------|
| Unit tests | `tests/test_*.py` | N/A | Logic bugs, parameter validation |
| Structural E2E | `tests/e2e/workshop.spec.ts`, `tests/e2e/analysis-workflow.spec.ts` | Yes | UI regressions, template errors, JS crashes |
| Smoke E2E | `tests/e2e/smoke.spec.ts` | **No** | Real API failures, auth errors, broken deployments |

## Running Tests

```bash
# Quick: unit tests only
uv run pytest -v

# Full: unit + structural E2E
uv run pytest -v && npx playwright test --grep-invert Smoke --project="Desktop Edge"

# Complete: everything including live smoke
uv run pytest -v && npx playwright test --project="Desktop Edge"
```

## Key Files

- `src/workshop/server.py` — FastAPI app with all routes
- `src/workshop/routers/` — API endpoints (DI, CU, documents, health)
- `src/workshop/services/` — Azure SDK integration (DI, CU, trace)
- `src/workshop/templates/` — Jinja2 HTML templates with Alpine.js
- `tests/e2e/helpers.ts` — Shared console error detection fixture
- `playwright.config.ts` — E2E test config (targets deployed Azure Container App)

## Common Failure Modes

1. **"Analysis Failed — Internal Server Error"** — Azure AI services endpoint misconfigured or credentials expired
2. **"Unexpected token" errors** — API returning HTML/plain text instead of JSON
3. **Console errors** — JS crash in Alpine.js reactive code, usually from unexpected API response shapes
4. **Blank result panels** — API returns success but with empty/malformed result structure

## Environment

- Python 3.12 with uv package manager
- Node.js with Playwright (Edge browser)
- Azure AI Services (Document Intelligence + Content Understanding)
- Deployed to Azure Container Apps
