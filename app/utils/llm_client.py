"""
Thin wrapper so agents don't care whether they're talking to Groq, OpenAI, or
nothing at all. If MOCK_MODE is on (or no key is configured), we fall back to
a deterministic parser -- this is what keeps a live demo alive if the venue's
wifi or API access is unreliable.
"""
import json
import re
from typing import Optional

from app.config import settings

EXTRACTION_PROMPT = """You are an invoice-parsing assistant. Extract structured data from the
raw invoice text below and return ONLY valid JSON with this exact shape:

{{
  "vendor_name": string,
  "invoice_number": string or null,
  "invoice_date": string or null,
  "category": string or null,
  "total_amount": number,
  "line_items": [{{"description": string, "quantity": number, "unit_price": number, "amount": number}}]
}}

Raw invoice text:
---
{raw_text}
---
Return only the JSON object, no commentary.
"""


def extract_invoice_fields(raw_text: str) -> dict:
    if settings.mock_mode or settings.llm_provider == "mock":
        return _mock_extract(raw_text)
    return _llm_extract(raw_text)


def _llm_extract(raw_text: str) -> dict:
    """Real call, used when MOCK_MODE=false and a provider key is configured."""
    import litellm

    model = settings.llm_model
    kwargs = {}
    if settings.llm_provider == "groq":
        model = f"groq/{model}"
        api_key = settings.groq_api_key
    else:
        api_key = settings.openai_api_key
        # OpenAI's JSON mode forces the model to return a syntactically valid
        # JSON object, which removes most of the "model added a stray
        # sentence before the JSON" failure modes we'd otherwise have to
        # clean up by hand.
        kwargs["response_format"] = {"type": "json_object"}

    response = litellm.completion(
        model=model,
        api_key=api_key,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(raw_text=raw_text)}],
        temperature=0,
        **kwargs,
    )
    content = response["choices"][0]["message"]["content"]
    return _parse_json_response(content)


def _parse_json_response(content: str) -> dict:
    """
    Robustly pull a JSON object out of an LLM response. Handles the common
    failure modes: markdown code fences, and stray commentary before/after
    the JSON that some models add even when told not to.
    """
    cleaned = content.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.MULTILINE).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fallback: grab the first '{' through the last '}' and try again.
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from LLM response: {content[:300]!r}")


def _mock_extract(raw_text: str) -> dict:
    """
    Deterministic parser for a simple 'Key: Value' style invoice format.
    Not an LLM -- exists so the pipeline is fully demoable offline and so
    the rules engine / DB / API can be tested without burning API calls.
    """
    def grab(pattern: str, default: Optional[str] = None) -> Optional[str]:
        m = re.search(pattern, raw_text, re.IGNORECASE)
        return m.group(1).strip() if m else default

    vendor = grab(r"Vendor:\s*(.+)")
    invoice_number = grab(r"Invoice Number:\s*(.+)")
    date = grab(r"Date:\s*(.+)")
    category = grab(r"Category:\s*(.+)")
    total_raw = grab(r"Total:\s*\$?([\d,.]+)", "0")
    total_amount = float(total_raw.replace(",", "")) if total_raw else 0.0

    line_items = []
    for m in re.finditer(r"-\s*(.+?)\s*x(\d+(?:\.\d+)?)\s*@\s*\$?([\d,.]+)", raw_text):
        desc, qty, price = m.group(1).strip(), float(m.group(2)), float(m.group(3))
        line_items.append({
            "description": desc,
            "quantity": qty,
            "unit_price": price,
            "amount": round(qty * price, 2),
        })

    return {
        "vendor_name": vendor or "Unknown Vendor",
        "invoice_number": invoice_number,
        "invoice_date": date,
        "category": category,
        "total_amount": total_amount,
        "line_items": line_items,
    }
