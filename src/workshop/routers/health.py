"""Health check endpoint."""

from fastapi import APIRouter, Query

from workshop.config import settings

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health(deep: bool = Query(False)) -> dict[str, object]:
    result: dict[str, object] = {
        "status": "ok",
        "environment": settings.environment,
    }
    if not deep:
        return result

    services: dict[str, dict[str, bool]] = {
        "ai_services_endpoint": {"configured": bool(settings.ai_services_endpoint)},
        "storage_account_url": {"configured": bool(settings.storage_account_url)},
    }
    all_configured = all(svc["configured"] for svc in services.values())
    result["status"] = "ok" if all_configured else "degraded"
    result["services"] = services
    return result
