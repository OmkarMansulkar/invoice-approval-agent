from typing import TypedDict, List, Optional, Any


class AgentState(TypedDict, total=False):
    raw_text: str
    extracted: dict            # output of the extractor agent
    decision: str               # "approved" | "rejected" | "needs_review"
    reason: Optional[str]
    trace: List[dict]           # ordered log of what each agent did, for the audit trail
    error: Optional[str]
    invoice_id: Optional[int]   # set by the approver node once the row is persisted
