from fastapi import FastAPI

from app.db.database import init_db
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.auth_middleware import APIKeyMiddleware
from app.api.routes_invoices import router as invoices_router

app = FastAPI(
    title="Invoice Approval Agent",
    description="Multi-agent invoice extraction, rule validation, and approval pipeline.",
    version="1.0.0",
)

# Order matters: outermost middleware added last runs first on the way in.
app.add_middleware(APIKeyMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(invoices_router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
