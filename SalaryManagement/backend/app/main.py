"""FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import APIError

app = FastAPI(
    title=settings.app_name,
    description="Employee and Salary Management Platform for ACME",
    version="1.0.0",
    debug=settings.debug,
)

# All versioned application endpoints.
app.include_router(
    api_router,
    prefix="/api/v1",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return validation errors using the standard API error structure."""

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": jsonable_encoder(exc.errors()),
            }
        },
    )


@app.exception_handler(APIError)
async def application_error_handler(
    request: Request,
    exc: APIError,
) -> JSONResponse:
    """Serialize application exceptions consistently."""

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Report application process liveness."""

    return {"status": "ok"}
