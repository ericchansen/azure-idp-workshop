# Routing Rules

## Signal → Agent

| Signal | Agent(s) |
|--------|----------|
| FastAPI routes, Python services, API endpoints, server.py | Hicks |
| HTML templates, Alpine.js, Tailwind, Jinja2, UI/UX | Lambert |
| Azure DI, Azure CU, Document Intelligence, Content Understanding, AI services, model comparison | Bishop |
| Playwright tests, pytest, E2E, test coverage, quality | Vasquez |
| Architecture, scope, code review, multi-domain decisions | Ripley |
| Module strategy, workshop narrative, demo flow | Ripley + Bishop |
| Backend + Frontend coordination | Hicks + Lambert |
| Full stack feature | Ripley (architect) → Hicks + Lambert (implement) → Vasquez (test) |

## File Ownership

| Path Pattern | Primary | Secondary |
|--------------|---------|-----------|
| `src/workshop/server.py` | Hicks | Ripley |
| `src/workshop/routers/*.py` | Hicks | Bishop |
| `src/workshop/services/*.py` | Hicks | Bishop |
| `src/workshop/templates/*.html` | Lambert | — |
| `src/workshop/static/**` | Lambert | — |
| `src/workshop/config.py` | Hicks | — |
| `tests/test_*.py` | Vasquez | Hicks |
| `tests/e2e/*.spec.ts` | Vasquez | Lambert |
| `playwright.config.ts` | Vasquez | — |
| `infra/**` | Ripley | Hicks |
| `Dockerfile` | Hicks | Ripley |
| `AGENTS.md`, `README.md` | Ripley | — |
