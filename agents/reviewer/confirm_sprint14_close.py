"""Ingrid's final close confirmation for Sprint 14 -- the formal review-
gate row (`db.create_review`, result must be 'approved') that
`log_sprint.py` checks before a sprint can be marked completed. Distinct
from her earlier content review of the synthesis (REVISE verdict,
already addressed) -- this checks that the specific revision was applied
correctly and that Sophie's three closing decisions are properly
reflected before the sprint formally closes.

Verdict parsing uses a precise regex on the final line, not a fuzzy
substring check -- real bug already caught and fixed once this sprint
(gate_sprint14_registrar_lock.py matched a section header instead of the
real verdict line); same discipline applied here from the start.
"""
import os
import re

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"

SOPHIE_DECISIONS = """Sophie's three sprint-closing decisions (2026-09-16):
1. Sprint-closing criterion: YES, the FVBS main result is sufficient to close on.
   Sprint 14's scope (Backlog #38) was the audience-optimal rerun and a
   quantitative verdict on whether models choose audience-optimally --
   delivered, pre-registered, within band, gate-reviewed. Mechanism-level
   H6 questions are explicitly out of scope for this sprint.
2. NOT-IN-SET disaggregation: current three-cause breakdown is sufficient
   to close on. Per-scenario disaggregation is deferred to a new backlog
   item (medium priority), not a Sprint 14 blocker.
3. N=3 stratum anomaly: NOT drilled down further before close. Documented
   as a clearly-marked small-N anomaly, logged as a new backlog item (low
   priority) rather than investigated now -- explicitly to avoid the
   Reported-Success Trap in reverse (over-explaining an unstable result).
"""


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")

    sprint_id = db.get_sprint_id(14)
    if sprint_id is None:
        sprint_id = db.create_sprint(14, "Backlog #38: rerun with an audience-optimal (FVBS) criterion")

    revised_synthesis = db.get_memory("kenji", "sprint14_synthesis") or ""
    original_review = db.get_memory("ingrid", "sprint14_synthesis_review") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Sprint 14 close confirmation",
        description="Formal review-gate row before Sophie can close the sprint.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=4000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Final close confirmation for Sprint 14. You already reviewed "
            "the synthesis once (verdict REVISE, targeted) -- Kenji has "
            "now revised it. Check specifically:\n\n"
            "1. Was your required fix actually applied? (Section 2 must "
            "now state the criterion confirmation plainly -- 'confirms', "
            "not 'consistent with' -- while keeping the mechanism "
            "question open.)\n"
            "2. Were the 3 minor fixes applied (S06/S11 computability "
            "note; 'coherent cluster' instead of 'non-trivial proportion'; "
            "the softened gemini phrasing)?\n"
            "3. Do Sophie's three closing decisions below appropriately "
            "dispose of the open items from your review (sprint-closing "
            "criterion, NOT-IN-SET disaggregation, N=3 stratum)?\n\n"
            f"{SOPHIE_DECISIONS}\n\n"
            "End your response with EXACTLY one final line, nothing after "
            "it: either 'FINAL VERDICT: APPROVED' or "
            "'FINAL VERDICT: NEEDS_REVISION'.\n\n"
            f"=== YOUR ORIGINAL REVIEW (verbatim) ===\n{original_review}\n\n"
            f"=== REVISED SYNTHESIS (v2) ===\n{revised_synthesis}\n"
        )}],
    )
    review = result.text
    db.log_usage("ingrid", result.input_tokens, result.output_tokens)

    m = re.search(r"FINAL VERDICT:\s*(APPROVED|NEEDS_REVISION)", review.upper())
    result_label = "approved" if (m and m.group(1) == "APPROVED") else "needs_revision"

    db.create_review(
        sprint_id=sprint_id, task_id=task_id, reviewer_agent="ingrid",
        result=result_label, notes={"memory_key": "ingrid/sprint14_close_confirmation"},
    )
    db.set_memory("ingrid", "sprint14_close_confirmation", review)
    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"sprint14-close-confirmation-task-{task_id}",
        text=review,
        metadata={"agent": "ingrid", "type": "sprint14_close_confirmation"},
    )
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/sprint14_close_confirmation", "result": result_label},
    )

    print(f"[{NAME}] sprint_id={sprint_id}, result={result_label}\n\n{review}")
    print(f"\n\n--- stored as ingrid/sprint14_close_confirmation, reviews row created ---")


if __name__ == "__main__":
    run()
