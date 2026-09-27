from app.rules.engine import RulesEngine


def test_small_approved_vendor_invoice_is_approved():
    engine = RulesEngine()
    invoice = {
        "vendor_name": "Staples",
        "total_amount": 67.0,
        "category": "Office Supplies",
    }
    result = engine.evaluate(invoice)
    assert result.decision == "approved"


def test_unapproved_vendor_needs_review():
    engine = RulesEngine()
    invoice = {
        "vendor_name": "Random Vendor LLC",
        "total_amount": 3200.0,
        "category": "Software",
    }
    result = engine.evaluate(invoice)
    assert result.decision == "needs_review"


def test_huge_amount_is_rejected():
    engine = RulesEngine()
    invoice = {
        "vendor_name": "Globex Inc",
        "total_amount": 13000.0,
        "category": "Equipment",
    }
    result = engine.evaluate(invoice)
    assert result.decision == "rejected"


def test_travel_conditional_rule_only_applies_to_travel():
    engine = RulesEngine()
    non_travel = {"vendor_name": "Acme Corp", "total_amount": 1450.0, "category": "Software"}
    travel = {"vendor_name": "Acme Corp", "total_amount": 1450.0, "category": "Travel"}

    # Non-travel: 1450 is under the 2000 auto-approve ceiling and vendor is approved -> approved
    assert engine.evaluate(non_travel).decision == "approved"
    # Travel: same amount, but travel rule caps at 1000 -> needs_review
    assert engine.evaluate(travel).decision == "needs_review"


def test_missing_category_flags_for_review():
    engine = RulesEngine()
    invoice = {"vendor_name": "Acme Corp", "total_amount": 50.0, "category": ""}
    result = engine.evaluate(invoice)
    assert result.decision == "needs_review"
