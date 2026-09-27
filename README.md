# Invoice Approval Agent

A multi-agent invoice processing pipeline: raw invoice text goes in, a chain of
agents extracts the data, validates it against configurable business rules,
and persists a final approve/reject/needs-review decision with a full audit
trail.

## Architecture

```
Raw invoice text
      |
      v
 [Extractor Agent]  -- parses vendor, amount, line items, category
      |
      v
 [Validator Agent]  -- runs extracted data through RulesEngine (app/rules/)
      |
      v
 [Approver Agent]   -- persists Invoice, LineItems, Approval, AuditLog to DB
      |
      v
   SQLite DB
```

The three agents are wired together as a **LangGraph** `StateGraph`
(`app/agents/graph.py`) — a straight pipeline on purpose, so it's easy to
explain and easy to extend (e.g. adding a "notifier" node is one new node +
one new edge).

## Folder structure

```
app/
  main.py                 FastAPI app: middleware + router registration
  config.py                Settings loaded from .env
  db/
    database.py             SQLAlchemy engine/session
    models.py                Schema: Invoice, LineItem, Approval, AuditLog
    schemas.py                Pydantic request/response models
  rules/
    rules.json                 Business rules (edit this, not code, to change policy)
    engine.py                   RulesEngine: loads rules.json, evaluates an invoice
  agents/
    state.py                     Shared AgentState schema
    extractor.py                  Extractor agent node
    validator.py                   Validator agent node
    approver.py                     Approver agent node (writes to DB)
    graph.py                         LangGraph wiring
  middleware/
    logging_middleware.py         Logs method/path/status/duration for every request
    auth_middleware.py             Simple X-API-Key header check
  api/
    routes_invoices.py            REST endpoints
  utils/
    llm_client.py                 Real LLM call OR deterministic mock (see below)
sample_invoices/            4 example invoices covering approve/review/reject/conditional
seed_demo_data.py           Runs the sample invoices through the pipeline to pre-populate the DB
tests/test_rules_engine.py  Unit tests for the rules engine (no API key needed)
```

## Database schema

- **invoices** (id, vendor_name, invoice_number, invoice_date, category, total_amount, status)
- **line_items** (id, invoice_id FK, description, quantity, unit_price, amount)
- **approvals** (id, invoice_id FK, decision, reason, decided_by) — one-to-one with invoice
- **audit_logs** (id, invoice_id FK, step, detail, timestamp) — one row per agent step

## The rules engine

`app/rules/rules.json` defines policy as data, not code:

```json
{
  "id": "max_auto_approve_amount",
  "field": "total_amount",
  "operator": "lte",
  "value": 2000,
  "severity": "review"
}
```

`RulesEngine.evaluate()` runs every rule against the extracted invoice fields
and returns a decision:
- any `"reject"` severity violation → **rejected**
- else any `"review"` severity violation → **needs_review**
- else → **approved**

Rules can also be conditional (`only_if`), e.g. the travel-spend cap only
applies when `category == "Travel"`. This is the piece an interviewer can
reasonably ask you to change live — e.g. "lower the auto-approve limit to
$500" is a one-line JSON edit.

## Demo-safety: mock mode

`MOCK_MODE=true` in `.env` (the default) makes the extractor agent use a
deterministic regex-based parser instead of calling a real LLM. This means:
- the entire pipeline runs with **zero API keys and no internet**
- the demo can't fail because of flaky wifi at the interview venue
- setting `MOCK_MODE=false` and providing `GROQ_API_KEY` or `OPENAI_API_KEY`
  switches to a real LLM call with no other code changes

## Running it

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Pre-populate the DB with sample invoices (optional but recommended before a demo)
python seed_demo_data.py

# Run the API
uvicorn app.main:app --reload
```

Then, with the server running:

```bash
# List invoices (requires the API key from .env)
curl -H "X-API-Key: demo-secret-key" http://127.0.0.1:8000/invoices

# Submit a new invoice through the full agent pipeline
curl -X POST -H "X-API-Key: demo-secret-key" -H "Content-Type: application/json" \
  -d '{"raw_text": "Vendor: Staples\nInvoice Number: INV-1\nCategory: Office Supplies\nLine Items:\n- Pens x5 @ 2.00\nTotal: 10.00"}' \
  http://127.0.0.1:8000/invoices/submit

# Interactive API docs
open http://127.0.0.1:8000/docs
```

Run the rules engine tests (no server or API keys needed):

```bash
python -m pytest tests/ -v
```

## Talking points for a live-modification demo

A few small, well-contained changes that are easy to plan out loud and
execute live:

1. **Add a new rule** — e.g. require manager approval for any invoice from a
   brand-new vendor not in the approved list, by editing `rules.json` and
   adding a test case.
2. **Add a new agent node** — e.g. a "Notifier" agent after Approver that
   would send a Slack/email alert for rejected invoices (stub is enough:
   show where it plugs into `graph.py`).
3. **Extend the schema** — e.g. add a `currency` column to `Invoice` and
   thread it through extractor → validator → approver.
4. **Swap mock mode for a real LLM call** — flip `MOCK_MODE=false`, set an
   API key, and show the same pipeline now using a real model.
