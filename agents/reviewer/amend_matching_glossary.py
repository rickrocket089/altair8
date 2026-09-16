"""Ingrid amends the matching-rule glossary per Kenji's Phase 1 pilot
assessment (kenji/sprint14_phase1_assessment), which found 2 real gaps
while trial-scoring the pilot outputs: compound co-equal labels spanning
two mark families, and multi-panel composite nominations with no
designated primary panel. Per the glossary's own sign-off ("the glossary
does not grow during scoring; it grows only through the amendment
process, and every amendment is a locked event in the record"), this is
that amendment process -- not an ad hoc fix.

Re-hashes and re-locks the full amended document.
"""
import hashlib
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")

    glossary = db.get_memory("ingrid", "sprint14_matching_glossary") or ""
    assessment = db.get_memory("kenji", "sprint14_phase1_assessment") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Amend the matching-rule glossary per Kenji's Phase 1 pilot findings",
        description="2 real gaps found while trial-scoring pilot outputs: compound co-equal labels, multi-panel composites.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=6000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Kenji's Phase 1 pilot assessment trial-scored the 36-call "
            "pilot against your matching-rule glossary and found 2 real "
            "gaps -- real model outputs your glossary did not cleanly "
            "resolve, correctly escalated rather than forced. Per your "
            "own sign-off, this is a formal amendment, not an ad hoc "
            "fix.\n\n"
            "CASE 1 (from S03 | ORDER-BEFORE | gpt-5.2): 'connected dot "
            "plot (slope chart over time)' -- a compound label where the "
            "model uses two co-equal names from different families "
            "(point-family: 'connected dot plot'; line-family: 'slope "
            "chart') in a single nomination, with neither clearly "
            "primary. Your existing tie-break rules resolve 'connected "
            "scatter plot vs line chart' only when one is described as "
            "primary and the other secondary -- not this genuinely "
            "co-equal case.\n\n"
            "CASE 2 (from S08 | BASELINE | claude-sonnet-4-6): a "
            "multi-panel composite nomination where Panel 1 was "
            "described as a filled area chart and Panel 2 as a bar "
            "chart, encoding the same data split across two different "
            "mark families with neither panel designated primary. Your "
            "glossary's composite handling (5.1, 7.6) doesn't cover this "
            "shape.\n\n"
            "Write two new glossary entries (in the same style/format as "
            "the existing Section 7 tie-break entries) that resolve these "
            "cases going forward:\n\n"
            "- Entry for CO-EQUAL COMPOUND LABELS spanning two families: "
            "state the resolution rule. Consider whether a determinate "
            "match is ever appropriate here or whether this should always "
            "escalate -- and if it should always escalate, say so plainly "
            "rather than inventing a false tie-break.\n\n"
            "- Entry for MULTI-PANEL COMPOSITES with cross-family panels "
            "and no designated primary: state the resolution rule, "
            "including whether the Blind Scorer should use the "
            "scenario's encoded_fields list to determine which panel "
            "addresses the primary variable, and what happens if that "
            "still doesn't resolve it.\n\n"
            "Write these as a clearly marked AMENDMENT section to append "
            "to the existing glossary (do not rewrite what already "
            "works). Close with a short amendment sign-off: what "
            "prompted this amendment, that it was found during Phase 1 "
            "piloting rather than Phase 2 scoring (the reason piloting "
            "exists), and that the amended document is what re-locks "
            "before Phase 2.\n\n"
            f"=== EXISTING GLOSSARY (FULL, for context -- do not repeat "
            f"it, just append your amendment) ===\n{glossary[-6000:]}\n\n"
            f"=== KENJI'S RELEVANT FINDING (for exact case detail) ===\n"
            f"{assessment[assessment.find('Cases that required escalation'):assessment.find('Check 6')][:3000]}\n"
        )}],
    )
    amendment = result.text
    db.log_usage("ingrid", result.input_tokens, result.output_tokens)

    amended_glossary = glossary + "\n\n---\n\n" + amendment
    digest = hashlib.sha256(amended_glossary.encode("utf-8")).hexdigest()

    db.set_memory("ingrid", "sprint14_matching_glossary", amended_glossary)
    db.set_memory("ingrid", "sprint14_matching_glossary_sha256", digest)
    db.set_memory("ingrid", "sprint14_matching_glossary_amendment_1", amendment)

    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"matching-glossary-amendment-task-{task_id}",
        text=amendment,
        metadata={"agent": "ingrid", "type": "sprint14_matching_glossary_amendment"},
    )
    db.update_task(
        task_id, status="completed", result=f"Amended, re-hashed. New SHA-256: {digest}",
        artifact_type="glossary_amendment",
        artifact_payload={"memory_key": "ingrid/sprint14_matching_glossary"},
    )

    print(f"[{NAME}] Re-locked. New SHA-256: {digest}\n\n{amendment}")
    print(f"\n\n--- stored as ingrid/sprint14_matching_glossary (amended, re-hashed) ---")


if __name__ == "__main__":
    run()
