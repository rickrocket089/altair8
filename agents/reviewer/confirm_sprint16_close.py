"""Ingrid's Sprint 16 close gate. Per Sophie's own Phase 0 process design,
her one specific job here: is Sprint 17's scope (Plan A) actually small
enough, or does it risk becoming another elaborate testbed -- the exact
failure mode the founder's original critique was reacting against
(Sprint 13/14's methodology growing past the question it was meant to
answer). Also the formal review-gate row required before the sprint can
be marked completed.
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

    sprint_id = db.get_sprint_id(16)
    if sprint_id is None:
        sprint_id = db.create_sprint(16, "Reconceiving FGE beyond Draco -- browser-native generative vocabulary + composition")

    synthesis = db.get_memory("team_leader", "sprint16_synthesis") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Sprint 16 close gate: is Sprint 17's scope small enough?",
        description="Formal review-gate row before Sophie can close Sprint 16 / open Sprint 17.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=5000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Sprint 16 close gate. Sophie's synthesis (below) is the "
            "complete deliverable package -- Concept Spec, prior-art "
            "memo, Sprint 17 transition plan, open questions. Your "
            "specific job, per the sprint's own process design: is "
            "Sprint 17's scope (Plan A) actually small enough, or does "
            "it risk becoming another elaborate testbed -- the exact "
            "failure mode the founder's original critique reacted "
            "against (Sprint 13/14's FVBS/Registrar/Blind-Scorer "
            "machinery growing past the question it was meant to "
            "answer)?\n\n"
            "CHECK 1 -- SCOPE SIZE. Sprint 17 as specified: a rendering-"
            "environment declaration, a contract checker (predicate "
            "evaluator, no solver, no planner), a founder submission + "
            "infer-then-confirm workflow, SQLite storage, all 8 seed "
            "contracts run through the checker. Is this genuinely small "
            "and testable, or is the '8 seed contracts + a full "
            "submission/inference/confirmation UI workflow' actually "
            "more than 'the smallest thing that tests checkability' "
            "would require? If you think it should be cut further, say "
            "exactly what to cut and why -- don't just gesture at "
            "'maybe smaller.'\n\n"
            "CHECK 2 -- THE BEHAVIORAL-GRAVITY RISK, TAKEN SERIOUSLY. "
            "Sophie's own honest assessment says the architecture solves "
            "the Draco-vocabulary contradiction but not the risk that "
            "practice stays chart-dominated (5 chart contracts vs. 3 "
            "non-chart, source-tier-prior-capture predicted to favor "
            "charts). Does Sprint 17's plan, as scoped, actually protect "
            "against this, or does it just note the risk and proceed "
            "unchanged? Is there a concrete, cheap addition to Sprint "
            "17's scope that would meaningfully test the non-chart "
            "contracts' checkability specifically (not just include them "
            "in a list), or is the current plan adequate as-is?\n\n"
            "CHECK 3 -- THE FOUR OPEN QUESTIONS. Confirm each of the 4 "
            "flagged open questions (Minto/Zelazny tagging, MECE/"
            "vertical-logic contract addition, vocabulary-finalization "
            "dependency, checkability-bifurcation pre-build review) is "
            "genuinely a founder/Sophie/Priya-Kenji decision and not "
            "something that should have been resolved within Sprint 16 "
            "itself before closing.\n\n"
            "CHECK 4 -- PROCESS REVIEW STATUS. Verify via the real "
            "cadence facts whether a Process Review is due -- do not "
            "estimate.\n\n"
            f"REAL PROCESS REVIEW FACTS: {db.process_review_status_block()}\n\n"
            "GATE VERDICT: end with exactly one final line, nothing "
            "after it: either 'FINAL VERDICT: APPROVED' or "
            "'FINAL VERDICT: NEEDS_REVISION'.\n\n"
            f"=== SOPHIE'S SPRINT 16 SYNTHESIS (full) ===\n{synthesis}\n"
        )}],
    )

    gate = result.text
    db.log_usage("ingrid", result.input_tokens, result.output_tokens)

    m = re.search(r"FINAL VERDICT:\s*(APPROVED|NEEDS_REVISION)", gate.upper())
    result_label = "approved" if (m and m.group(1) == "APPROVED") else "needs_revision"

    db.create_review(
        sprint_id=sprint_id, task_id=task_id, reviewer_agent="ingrid",
        result=result_label, notes={"memory_key": "ingrid/sprint16_close_gate"},
    )
    db.set_memory("ingrid", "sprint16_close_gate", gate)
    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"sprint16-close-gate-task-{task_id}",
        text=gate,
        metadata={"agent": "ingrid", "type": "sprint16_close_gate"},
    )
    db.update_task(
        task_id, status="completed", result=gate,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/sprint16_close_gate", "result": result_label},
    )

    print(f"[{NAME}] sprint_id={sprint_id}, result={result_label}\n\n{gate}")
    print(f"\n\n--- stored as ingrid/sprint16_close_gate, reviews row created ---")


if __name__ == "__main__":
    run()
