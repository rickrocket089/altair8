"""Ingrid's formal close-gate for Sprint 15 -- a real process gap caught
during Sprint 16's own close gate (2026-09-17): Sprint 15 was never
formally closed. Its real deliverable (Priya's 4 concepts, Kenji's
reality check, Ingrid's content review) is complete and was acted on
(the founder chose FGE, which then became Sprint 16's reconceived
Mechanism A) -- but the formal review-gate row and sprint completion
were never recorded, which is why Process Review cadence tracking went
stale.

This is the formal close-gate row required by the review-gate pattern
(mirrors confirm_sprint14_close.py), distinct from Ingrid's earlier
content review of the 4 concepts (which already ran and returned a
verdict on the concepts themselves, not on the sprint as a whole).
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


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")

    sprint_id = db.get_sprint_id(15)
    if sprint_id is None:
        raise RuntimeError("Sprint 15 not found in sprints table.")

    concepts_review = db.get_memory("ingrid", "sprint15_concepts_review") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Sprint 15 close gate (formal review-gate row, real process gap being closed)",
        description="Sprint 15 was never formally closed -- caught during Sprint 16's own close gate.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=3000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Formal close-gate confirmation for Sprint 15. You already "
            "reviewed the sprint's actual content (the 4 concepts: "
            "ACFR, FGE, AAEB, CCO) and returned a verdict: all 4 fit to "
            "go forward, with 2 pre-conditions (CCO's claim-"
            "identification mechanism, FGE's rendering-path "
            "confirmation) and 3 minor disclosure-gap fixes. This is a "
            "different, narrower check: is the SPRINT itself complete "
            "and closeable? Confirm:\n\n"
            "1. Was the deliverable (3-5 concepts, later 4) actually "
            "produced and reviewed? (Yes -- confirm from your own prior "
            "review.)\n"
            "2. Was the sprint's outcome actually acted on? (Yes -- the "
            "founder selected FGE, per Priya's own stated confidence "
            "ranking, which became Sprint 16's starting point.)\n"
            "3. Are there any unresolved blockers from your original "
            "concept review that would prevent marking Sprint 15 "
            "complete? (Note: the 2 pre-conditions you named were "
            "conditions on CCO/FGE's future IMPLEMENTATION, not "
            "conditions on Sprint 15's own concept-generation deliverable "
            "being complete -- confirm this reading is correct, or say "
            "if you think otherwise.)\n\n"
            "End with exactly one final line, nothing after it: either "
            "'FINAL VERDICT: APPROVED' or 'FINAL VERDICT: "
            "NEEDS_REVISION'.\n\n"
            f"=== YOUR ORIGINAL SPRINT 15 CONCEPTS REVIEW (verbatim) ===\n{concepts_review}\n"
        )}],
    )

    gate = result.text
    db.log_usage("ingrid", result.input_tokens, result.output_tokens)

    m = re.search(r"FINAL VERDICT:\s*(APPROVED|NEEDS_REVISION)", gate.upper())
    result_label = "approved" if (m and m.group(1) == "APPROVED") else "needs_revision"

    db.create_review(
        sprint_id=sprint_id, task_id=task_id, reviewer_agent="ingrid",
        result=result_label, notes={"memory_key": "ingrid/sprint15_close_gate"},
    )
    db.set_memory("ingrid", "sprint15_close_gate", gate)
    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"sprint15-close-gate-task-{task_id}",
        text=gate,
        metadata={"agent": "ingrid", "type": "sprint15_close_gate"},
    )
    db.update_task(
        task_id, status="completed", result=gate,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/sprint15_close_gate", "result": result_label},
    )

    print(f"[{NAME}] sprint_id={sprint_id}, result={result_label}\n\n{gate}")
    print(f"\n\n--- stored as ingrid/sprint15_close_gate, reviews row created ---")


if __name__ == "__main__":
    run()
