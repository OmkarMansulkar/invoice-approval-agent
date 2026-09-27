import time
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("invoice_agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f'{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)'
        )
        return response
