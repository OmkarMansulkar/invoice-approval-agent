"""
The agent pipeline: extractor -> validator -> approver.

This is deliberately a straight line (no branching) so it's easy to explain
and easy to modify live -- e.g. adding a fourth "notifier" node is a one-line
change to the edges below.
"""
from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.extractor import extractor_node
from app.agents.validator import validator_node
from app.agents.approver import approver_node


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("extractor", extractor_node)
    graph.add_node("validator", validator_node)
    graph.add_node("approver", approver_node)

    graph.set_entry_point("extractor")
    graph.add_edge("extractor", "validator")
    graph.add_edge("validator", "approver")
    graph.add_edge("approver", END)

    return graph.compile()


# Compiled once at import time and reused across requests.
invoice_agent_graph = build_graph()


def run_invoice_pipeline(raw_text: str) -> AgentState:
    initial_state: AgentState = {"raw_text": raw_text, "trace": []}
    return invoice_agent_graph.invoke(initial_state)
