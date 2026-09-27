from typing import List

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Invoice, AuditLog
from app.db.schemas import InvoiceSubmitRequest, InvoiceOut, AuditLogOut
from app.agents.graph import run_invoice_pipeline
from app.middleware.auth_middleware import api_key_header

# Every route below declares api_key_header as a dependency. It does not
# perform the actual check (APIKeyMiddleware already rejects bad requests
# before they reach here) -- it exists so /docs shows the Authorize button
# and sends whatever key you enter there as the X-API-Key header.
router = APIRouter(prefix="/invoices", tags=["invoices"], dependencies=[Security(api_key_header)])


@router.post("/submit", response_model=InvoiceOut)
def submit_invoice(payload: InvoiceSubmitRequest, db: Session = Depends(get_db)):
    """Run the full agent pipeline (extract -> validate -> approve) on raw invoice text."""
    final_state = run_invoice_pipeline(payload.raw_text)

    if final_state.get("error"):
        raise HTTPException(status_code=422, detail=f"Extraction failed: {final_state['error']}")

    invoice_id = final_state.get("invoice_id")
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    return invoice


@router.get("", response_model=List[InvoiceOut])
def list_invoices(db: Session = Depends(get_db)):
    return db.query(Invoice).order_by(Invoice.id.desc()).all()


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.get("/{invoice_id}/audit", response_model=List[AuditLogOut])
def get_audit_trail(invoice_id: int, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).filter(AuditLog.invoice_id == invoice_id).order_by(AuditLog.id).all()
    if not logs:
        raise HTTPException(status_code=404, detail="No audit trail found for this invoice")
    return logs
