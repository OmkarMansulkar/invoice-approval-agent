from app.agents.state import AgentState
from app.rules.engine import RulesEngine

# Single shared instance -- rules.json is read once at startup, reload() is
# available if you want to demo hot-reloading a rule change live.
rules_engine = RulesEngine()


def validator_node(state: AgentState) -> AgentState:
    """Run the extracted invoice fields through the rules engine."""
    trace = state.get("trace", [])
    if state.get("error"):
        return state  # extraction already failed, nothing to validate

    result = rules_engine.evaluate(state["extracted"])
    trace.append({
        "step": "validator",
        "detail": f"Decision candidate: {result.decision}. Reason: {result.reason}",
    })
    return {**state, "decision": result.decision, "reason": result.reason, "trace": trace}
