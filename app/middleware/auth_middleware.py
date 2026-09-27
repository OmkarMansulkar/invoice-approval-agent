from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings

# Paths that don't require an API key -- docs and health check should stay open.
OPEN_PATHS = {"/docs", "/openapi.json", "/redoc", "/health"}

# Declaring this (and using it as a route dependency, see routes_invoices.py)
# is purely so FastAPI registers a security scheme in the OpenAPI spec --
# that's what makes the "Authorize" button appear on the /docs page. The
# actual enforcement still happens below in APIKeyMiddleware.
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in OPEN_PATHS or request.url.path.startswith("/docs"):
            return await call_next(request)

        provided_key = request.headers.get("X-API-Key")
        if provided_key != settings.api_key:
            return JSONResponse(status_code=401, content={"detail": "Invalid or missing X-API-Key header"})

        return await call_next(request)
