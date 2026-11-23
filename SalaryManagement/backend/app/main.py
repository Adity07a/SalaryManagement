
from fastapi import FastAPI

from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    description="Employee and Salary Management Platform for ACME",
    version="1.0.0",
    debug=settings.debug,
)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """
    Application liveness endpoint.
    """

    return {
        "status": "ok",
    }
