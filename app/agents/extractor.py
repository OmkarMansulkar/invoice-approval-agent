from app.agents.state import AgentState
from app.utils.llm_client import extract_invoice_fields


def extractor_node(state: AgentState) -> AgentState:
    """Turn raw invoice text into structured fields."""
    trace = state.get("trace", [])
    try:
        extracted = extract_invoice_fields(state["raw_text"])
        trace.append({"step": "extractor", "detail": f"Extracted fields: {extracted}"})
        return {**state, "extracted": extracted, "trace": trace}
    except Exception as e:
        trace.append({"step": "extractor", "detail": f"Extraction failed: {e}"})
        return {**state, "error": str(e), "trace": trace}
