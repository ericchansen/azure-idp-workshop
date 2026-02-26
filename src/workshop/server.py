"""FastAPI application — Azure IDP Workshop."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from workshop.config import settings
from workshop.routers import cu, di, documents, health

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


# ── Page routes ──────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/module/1", response_class=HTMLResponse)
async def module_1(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("module1.html", {"request": request})


@app.get("/module/2", response_class=HTMLResponse)
async def module_2(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("module2.html", {"request": request})


@app.get("/module/3", response_class=HTMLResponse)
async def module_3(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("module3.html", {"request": request})


@app.get("/guide", response_class=HTMLResponse)
async def decision_guide(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("guide.html", {"request": request})
