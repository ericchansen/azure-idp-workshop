ARG PYTHON_BASE_IMAGE=python:3.12.11-slim-bookworm
FROM ${PYTHON_BASE_IMAGE} AS base

WORKDIR /app

# Patch OS-level vulnerabilities in every build
RUN apt-get update && apt-get upgrade -y --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.7.12 /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source
COPY src/ src/
COPY samples/ samples/
COPY README.md ./
RUN uv sync --frozen --no-dev

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "workshop.server:app", "--host", "0.0.0.0", "--port", "8080"]
