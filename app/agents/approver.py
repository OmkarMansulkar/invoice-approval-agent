from app.agents.state import AgentState
from app.db.database import SessionLocal
from app.db.models import Invoice, LineItem, Approval, AuditLog, InvoiceStatus


def approver_node(state: AgentState) -> AgentState:
    """
    Persist the invoice, its line items, the approval decision, and the full
    audit trail. This is the node that turns agent output into durable state.
    """
    trace = state.get("trace", [])
    db = SessionLocal()
    try:
        if state.get("error"):
            trace.append({"step": "approver", "detail": f"Skipped persistence due to error: {state['error']}"})
            return {**state, "trace": trace}

        extracted = state["extracted"]
        decision = state["decision"]

        invoice = Invoice(
            vendor_name=extracted.get("vendor_name") or "Unknown Vendor",
            invoice_number=extracted.get("invoice_number"),
            invoice_date=extracted.get("invoice_date"),
            category=extracted.get("category"),
            total_amount=extracted.get("total_amount", 0.0),
            status=InvoiceStatus(decision),
        )
        db.add(invoice)
        db.flush()  # get invoice.id before adding children

        for item in extracted.get("line_items", []):
            db.add(LineItem(
                invoice_id=invoice.id,
                description=item.get("description", ""),
                quantity=item.get("quantity", 1),
                unit_price=item.get("unit_price", 0),
                amount=item.get("amount", 0),
            ))

        db.add(Approval(
            invoice_id=invoice.id,
            decision=InvoiceStatus(decision),
            reason=state.get("reason"),
            decided_by="approver_agent",
        ))

        for entry in trace:
            db.add(AuditLog(invoice_id=invoice.id, step=entry["step"], detail=entry["detail"]))
        db.add(AuditLog(invoice_id=invoice.id, step="approver", detail=f"Final decision: {decision}"))

        db.commit()
        trace.append({"step": "approver", "detail": f"Persisted invoice #{invoice.id} with decision {decision}"})
        return {**state, "trace": trace, "invoice_id": invoice.id}
    finally:
        db.close()
