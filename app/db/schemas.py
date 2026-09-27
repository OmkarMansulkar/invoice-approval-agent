from typing import Optional, List
from pydantic import BaseModel


class InvoiceSubmitRequest(BaseModel):
    raw_text: str  # raw OCR/plaintext invoice content to be parsed by the agent pipeline


class LineItemOut(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float

    class Config:
        from_attributes = True


class ApprovalOut(BaseModel):
    decision: str
    reason: Optional[str] = None
    decided_by: str

    class Config:
        from_attributes = True


class InvoiceOut(BaseModel):
    id: int
    vendor_name: str
    invoice_number: Optional[str]
    invoice_date: Optional[str]
    category: Optional[str]
    total_amount: float
    status: str
    line_items: List[LineItemOut] = []
    approval: Optional[ApprovalOut] = None

    class Config:
        from_attributes = True


class AuditLogOut(BaseModel):
    step: str
    detail: Optional[str]

    class Config:
        from_attributes = True
