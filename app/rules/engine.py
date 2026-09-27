"""
A small, self-contained rules engine.

Design goal: rules live in a data file (rules.json), not in code. Adding a new
purchasing policy should mean editing JSON, not touching Python -- this is the
thing an interviewer can ask you to change live.
"""
import json
import os
from dataclasses import dataclass, field
from typing import Any, List, Optional


RULES_PATH = os.path.join(os.path.dirname(__file__), "rules.json")


@dataclass
class RuleViolation:
    rule_id: str
    description: str
    severity: str  # "review" or "reject"


@dataclass
class EvaluationResult:
    violations: List[RuleViolation] = field(default_factory=list)

    @property
    def decision(self) -> str:
        if any(v.severity == "reject" for v in self.violations):
            return "rejected"
        if any(v.severity == "review" for v in self.violations):
            return "needs_review"
        return "approved"

    @property
    def reason(self) -> Optional[str]:
        if not self.violations:
            return None
        return "; ".join(f"[{v.severity}] {v.description}" for v in self.violations)


OPERATORS = {
    "lte": lambda a, b: a is not None and a <= b,
    "gte": lambda a, b: a is not None and a >= b,
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
    "not_empty": lambda a, b: bool(a),
}


class RulesEngine:
    def __init__(self, rules_path: str = RULES_PATH):
        self.rules_path = rules_path
        self.rules = self._load_rules()

    def _load_rules(self) -> List[dict]:
        with open(self.rules_path, "r") as f:
            data = json.load(f)
        return data["rules"]

    def reload(self):
        """Re-read rules.json without restarting the app -- handy for a live demo."""
        self.rules = self._load_rules()

    def _check_condition(self, invoice: dict, field_name: str, operator: str, value: Any) -> bool:
        actual = invoice.get(field_name)
        op_fn = OPERATORS.get(operator)
        if op_fn is None:
            raise ValueError(f"Unknown operator: {operator}")
        # "lte"/"gte" pass the invoice's failing case as a *violation* when the
        # condition is NOT met, so callers invert appropriately (see evaluate()).
        return op_fn(actual, value)

    def evaluate(self, invoice: dict) -> EvaluationResult:
        """
        invoice: dict with keys like vendor_name, total_amount, category, etc.
        Returns an EvaluationResult with the final decision + human-readable reason.
        """
        result = EvaluationResult()

        for rule in self.rules:
            # Conditional rules only apply when their "only_if" clause matches.
            gate = rule.get("only_if")
            if gate:
                gate_met = self._check_condition(invoice, gate["field"], gate["operator"], gate["value"])
                if not gate_met:
                    continue

            passes = self._check_condition(invoice, rule["field"], rule["operator"], rule["value"])
            if not passes:
                result.violations.append(
                    RuleViolation(
                        rule_id=rule["id"],
                        description=rule["description"],
                        severity=rule["severity"],
                    )
                )

        return result
