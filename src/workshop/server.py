"""FastAPI application — Azure IDP Workshop."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from workshop.config import settings
from workshop.routers import ais, batch, cu, di, documents, health, patient_logs

# Logging
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

# Paths
SRC_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SRC_DIR / "templates"
STATIC_DIR = SRC_DIR / "static"

# App
app = FastAPI(
    title="Azure IDP Workshop",
    description="Interactive zero-to-hero workshop: Document Intelligence vs Content Understanding",
    version="0.1.0",
)

# Static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Routers
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(di.router)
app.include_router(cu.router)
app.include_router(ais.router)
app.include_router(batch.router)
app.include_router(patient_logs.router)


# ── Page routes ──────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")


@app.get("/module/1", response_class=HTMLResponse)
async def module_1(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "module1.html")


@app.get("/module/2", response_class=HTMLResponse)
async def module_2(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "module2.html")


@app.get("/module/3", response_class=HTMLResponse)
async def module_3(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "module3.html")


@app.get("/module/4", response_class=HTMLResponse)
async def module_4(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "module4.html")


@app.get("/guide", response_class=HTMLResponse)
async def decision_guide(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "guide.html")


@app.get("/patient-log", response_class=HTMLResponse)
async def patient_log_analyzer(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "patient_log.html")
