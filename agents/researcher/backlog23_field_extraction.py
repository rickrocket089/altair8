"""Extract structured field definitions (name, type, approximate cardinality)
from each of the 20 scenarios' D3-template data descriptions, so a real
synthetic DataFrame can be built per scenario for Draco.

Why an LLM call and not regex: the 20 descriptions are natural language
following the D3 template loosely, not identically ("2 categorical: X, Y"
vs "1 categorical: X -- 5 sectors" vs cardinality omitted entirely). This
becomes the actual Layer-1 ground truth input -- a silent mis-parse here
would corrupt every downstream score. Structured extraction with an
explicit self-check is safer than a regex that might match confidently on
the wrong thing.
"""
import json
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"


def run() -> None:
    require_tool("kenji", "write_brief")

    scenarios = json.loads(db.get_memory("kenji", "sprint13_scenarios_structured"))
    blocks = "\n\n".join(
        f"{sid}: {sc['data_description']}" for sid, sc in sorted(scenarios.items())
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=6000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "For each of the 20 scenario data descriptions below, extract a "
            "structured field list: for each variable mentioned, its "
            "field_name (short snake_case identifier, invented but clearly "
            "traceable to the description), its type, and if the "
            "description states or implies a specific cardinality (number "
            "of categories, number of rows/observations) for that field, "
            "its approximate_cardinality as an integer -- otherwise null.\n\n"
            "TYPE MUST BE ONE OF FOUR VALUES, not just categorical/"
            "continuous -- this distinction matters a lot downstream:\n"
            "- 'nominal': categories with no inherent order (facility "
            "site, treatment arm, product category, demographic group). "
            "Cardinality equaling row count here genuinely means 'this is "
            "an identifier, not analytically meaningful' (e.g. batch_id).\n"
            "- 'ordinal_or_temporal': a sequence with meaningful order -- "
            "years, months, weeks, any time-indexed axis, or an explicitly "
            "ordered category. CRITICAL: many of these will ALSO have "
            "cardinality equal to row count (e.g. 60 distinct years for 60 "
            "rows) -- that is normal and does NOT mean it's a meaningless "
            "identifier. Never confuse 'high cardinality' with 'not worth "
            "encoding' for this type -- an ordered sequence is usually the "
            "single most important field to encode (typically the x-axis).\n"
            "- 'continuous': numeric, meaningful magnitude.\n"
            "- 'boolean': binary.\n\n"
            "Also extract number_rows: a reasonable approximate total row "
            "count (use what's stated if given, otherwise infer a "
            "plausible number from context, e.g. '30 batches' -> "
            "number_rows=30; if nothing is stated or inferable, use 50 as "
            "a generic default).\n\n"
            "Be literal -- extract what the description actually says, "
            "don't invent fields it doesn't mention. If ambiguous about "
            "exact cardinality, use approximate_cardinality: null rather "
            "than guessing a specific number. If ambiguous between nominal "
            "and ordinal_or_temporal, look for explicit ordering language "
            "('ordered sequence', 'over time', 'monthly', 'annual', "
            "'weekly') -- if present, it's ordinal_or_temporal.\n\n"
            "Return ONLY a JSON object: "
            "{\"S01\": {\"number_rows\": 30, \"fields\": [{\"field_name\": "
            "\"batch_id\", \"type\": \"nominal\", \"approximate_cardinality\": 30}, "
            "...]}, \"S02\": {...}, ...}. No prose, no markdown fences, "
            "all 20 scenarios present.\n\n"
            f"=== 20 SCENARIO DATA DESCRIPTIONS ===\n{blocks}\n"
        )}],
    )

    raw = result.text.strip()
    import re
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
    parsed = json.loads(raw)  # will raise loudly if malformed -- don't silently accept

    missing = set(scenarios) - set(parsed)
    assert not missing, f"Extraction missing scenarios: {missing}"

    db.log_usage("kenji", result.input_tokens, result.output_tokens)
    db.set_memory("kenji", "sprint13_field_extraction", json.dumps(parsed, indent=2, ensure_ascii=False))
    print(f"[{NAME}] Extracted fields for {len(parsed)}/20 scenarios (continuations: {result.continuations})")
    for sid in sorted(parsed):
        f = parsed[sid]
        print(f"  {sid}: rows={f['number_rows']}, fields={[(x['field_name'], x['type']) for x in f['fields']]}")


if __name__ == "__main__":
    run()
