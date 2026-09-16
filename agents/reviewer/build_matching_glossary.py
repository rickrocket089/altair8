"""Ingrid produces the form-family matching-rule glossary Kenji's Phase 0
protocol requires (Section 5, Step 2) before Phase 1 begins, as part of
the same lock package as the rankings -- a real gap: it was not built
when the rankings were hash-locked (gate_sprint14_registrar_lock.py).
Caught while preparing the Phase 1 pilot assessment, before it became a
Blind Scorer problem instead of a Phase-0 one.

Purpose: the Blind Scorer must match a model's natural-language form
nomination ("horizontal bar chart", "scatter plot", "grouped line
chart"...) against the Registrar's locked candidate labels, which are
always one of Draco's 7 canonical mark types (point, bar, line, area,
text, tick, rect) -- confirmed as the complete real set across all 20
scenario packets. Matching is by form FAMILY, not exact string: the
protocol's own worked example is "horizontal bar chart" matches "bar
chart" but "stacked bar chart" does NOT match "bar chart" (different
form family, because stacking changes what the encoding actually shows).
This glossary makes that rule concrete and exhaustive enough for the
Blind Scorer to apply consistently without re-deriving it trial by trial.

Hash-locked alongside the rankings/pre-registration once produced --
this is exactly the kind of criterion that must be fixed before scoring
begins, same discipline as everything else pre-registered.
"""
import hashlib
import json
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"

MARK_FAMILIES = ["point", "bar", "line", "area", "text", "tick", "rect"]


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Sprint 14: form-family matching-rule glossary for the Blind Scorer",
        description="Protocol Section 5 Step 2 deliverable, missed at the original lock -- built now, before Phase 1 scoring.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=4000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Produce the form-family matching-rule glossary Kenji's Phase 0 "
            "protocol (Section 5, Step 2) requires, before any Blind "
            "Scorer work begins. This governs how the Blind Scorer matches "
            "a model's free-text form nomination against the Registrar's "
            "locked candidate labels, which are always exactly one of "
            "these 7 canonical Draco mark families -- confirmed as the "
            "complete real set across all 20 scenario candidate sets, no "
            "others occur:\n\n"
            f"{', '.join(MARK_FAMILIES)}\n\n"
            "GOVERNING RULE, from the protocol: matching is by form "
            "family, not exact label. Worked example given: 'horizontal "
            "bar chart' matches 'bar' -- 'stacked bar chart' does NOT "
            "match 'bar', it is a different form family, because stacking "
            "changes what the encoding actually shows (it no longer "
            "directly encodes one value per category on a shared "
            "baseline).\n\n"
            "For EACH of the 7 families, produce:\n"
            "1. A list of natural-language names/variants a model is "
            "realistically likely to use that DO match this family (e.g. "
            "for 'bar': 'bar chart', 'horizontal bar chart', 'column "
            "chart'...).\n"
            "2. A list of natural-language names that LOOK similar but do "
            "NOT match this family, with a one-sentence reason each tied "
            "to what actually changes in the encoding (e.g. 'stacked bar "
            "chart' does not match 'bar' -- reason).\n"
            "3. Any genuinely AMBIGUOUS name that could plausibly belong "
            "to more than one family, with the tie-break rule the Blind "
            "Scorer should apply (e.g. 'dot plot' vs 'point'/'tick' -- "
            "when is it which).\n\n"
            "Then state explicitly: any form a model might name that does "
            "not map to any of these 7 families at all (e.g. a pie chart, "
            "a treemap, a Sankey diagram, a table) is NOT a matching-rule "
            "question -- it is a NOT-IN-SET outcome per protocol Section "
            "5, Step 2, and the Blind Scorer should not try to force it "
            "into one of the 7 families. Confirm this boundary is clear "
            "from your glossary as written.\n\n"
            "End with a one-paragraph sign-off: this glossary is fixed "
            "before Phase 1 scoring begins, and any name the Blind Scorer "
            "encounters that isn't covered here should be escalated for a "
            "glossary amendment (hash-relocked), not resolved ad hoc "
            "trial by trial."
        )}],
    )
    glossary = result.text
    db.log_usage("ingrid", result.input_tokens, result.output_tokens)

    digest = hashlib.sha256(glossary.encode("utf-8")).hexdigest()
    db.set_memory("ingrid", "sprint14_matching_glossary", glossary)
    db.set_memory("ingrid", "sprint14_matching_glossary_sha256", digest)

    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"matching-glossary-task-{task_id}",
        text=glossary,
        metadata={"agent": "ingrid", "type": "sprint14_matching_glossary"},
    )
    db.update_task(
        task_id, status="completed", result=f"Glossary produced, SHA-256: {digest}",
        artifact_type="glossary",
        artifact_payload={"memory_key": "ingrid/sprint14_matching_glossary"},
    )

    print(f"[{NAME}] SHA-256: {digest}\n\n{glossary}")
    print(f"\n\n--- {len(glossary)} chars, stored as ingrid/sprint14_matching_glossary ---")


if __name__ == "__main__":
    run()
