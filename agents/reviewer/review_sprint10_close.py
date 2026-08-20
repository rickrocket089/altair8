"""Ingrid's formal close review for Sprint 10. Writes the reviews row.

log_sprint.py refuses to mark a sprint completed without an 'approved' row in
the reviews table for it. This is the hard gate adopted from AI-Scientist-v2 in
Sprint 3, and it has already blocked two closes in practice (Sprints 4 and 8),
so it is not ceremony.

Distinct from her earlier Sprint 10 reviews, which each checked one artifact:
the design before it ran, the Pass 1 input for blindness, the Pass 4 marking.
This asks whether the SPRINT is done -- whether its own success criteria were
met, whether the founder's decision rests on something real, and whether
anything should have blocked the close.

Her verdict is recorded as she gives it. If she says needs_revision, the sprint
does not close, and that is the gate working rather than a problem to route
around.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

SPRINT_NUMBER = 10


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")
    sprint_id = db.get_sprint_id(SPRINT_NUMBER)

    proposal = db.get_memory("team_leader", "sprint10_proposal") or ""
    synthesis = db.get_memory("team_leader", "sprint10_synthesis") or ""
    verification = db.get_memory("kenji", "sprint10_concept_verification") or ""
    restated = db.get_memory("priya", "sprint10_restated_claims") or ""
    buildability = db.get_memory("mateo", "sprint10_buildability") or ""
    blind_gate = db.get_memory("ingrid", "sprint10_pass1_blindness_gate") or ""

    backlog = "\n".join(
        f"  [{i['priority']}] {i['title']}"
        for i in db.list_backlog_items() if i["status"] == "open"
    )

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Close review: Sprint 10",
        description="Formal review gate. The sprint cannot close without an approved verdict.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=12000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Formal close review for Sprint 10. log_sprint.py will not mark "
            "the sprint completed without an 'approved' verdict from you. You "
            "have blocked two closes before (Sprints 4 and 8) -- this is a "
            "real gate, and if this sprint should not close, say so.\n\n"
            "THE FOUNDER HAS CHOSEN C1 (The Commitment Audit) as the "
            "direction. Sprint 11 would build it.\n\n"
            "You have already reviewed three things in this sprint "
            "separately: the design before it ran, the Pass 1 input for "
            "blindness, and the Pass 4 marking. Do not re-litigate those. "
            "This is about whether the sprint is DONE.\n\n"
            "Judge:\n\n"
            "1. SUCCESS CRITERIA. The sprint set four. (a) at least 3 "
            "concepts complete across all fields -- you already confirmed "
            "this met. (b) each concept's falsification test judged buildable "
            "by Mateo within roughly one sprint -- 2 buildable, 2 not, 1 "
            "cannot judge, so as literally written this FAILED. (c) a "
            "prior-art verdict for every concept -- met, across two retrieval "
            "rounds. (d) the founder can make an actual choice -- he has. "
            "Does a sprint that failed criterion (b) as written deserve to "
            "close? Give a real answer, not a diplomatic one. If (b) was a "
            "badly-written criterion rather than a failed one, say that, and "
            "say what it should have been.\n\n"
            "2. THE DECISION ITSELF. C1 is the concept with the best-evidenced "
            "novelty position AND one of only two with a runnable "
            "falsification test. Is that a sound basis for choosing, or did "
            "the team's own capability limits pick the winner rather than the "
            "concept's merit? Be direct about this. It matters more than "
            "anything else in this review.\n\n"
            "3. Priya self-flagged a prior-art risk to C1 that Kenji did not "
            "catch: argument-mapping tools (Rationale, Compendium) in the HCI "
            "literature, never retrieved. C1 is now the chosen direction. "
            "Should that gap block the close, block the build, or be carried "
            "as a known risk?\n\n"
            "4. Anything the sprint got away with. This sprint ran four "
            "passes, two retrieval rounds and four review gates in a compressed "
            "period. Where was the thinking thinnest? What would you expect a "
            "Process Review to find here at Sprint 12?\n\n"
            "5. The backlog written at close (below) -- does it capture what "
            "actually needs carrying forward, or is something missing?\n\n"
            f"=== PROPOSAL (v2 + amendment) ===\n{proposal[:14000]}\n\n"
            f"=== YOUR OWN BLINDNESS GATE VERDICT ===\n{blind_gate[:6000]}\n\n"
            f"=== KENJI'S VERIFICATION (round 2) ===\n{verification[:22000]}\n\n"
            f"=== MATEO'S BUILDABILITY ===\n{buildability}\n\n"
            f"=== PRIYA'S RESTATED CLAIMS ===\n{restated[:12000]}\n\n"
            f"=== SOPHIE'S SYNTHESIS ===\n{synthesis[:16000]}\n\n"
            f"=== BACKLOG LOGGED AT CLOSE ===\n{backlog}\n\n"
            "End with exactly one of: APPROVED — sprint may close, or "
            "NEEDS_REVISION — with what must happen first."
        )}],
    ) as stream:
        response = stream.get_final_message()

    review = response.content[0].text
    db.log_usage("ingrid", response.usage.input_tokens, response.usage.output_tokens)

    upper = review.upper()
    if "NEEDS_REVISION" in upper and "APPROVED — SPRINT MAY CLOSE" not in upper:
        result = "needs_revision"
    elif "APPROVED" in upper:
        result = "approved"
    else:
        result = "needs_revision"

    db.create_review(
        sprint_id=sprint_id, task_id=task_id, reviewer_agent="ingrid",
        result=result, notes={"memory_key": "ingrid/sprint10_close_review"},
    )
    db.set_memory("ingrid", "sprint10_close_review", review)
    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"review-task-{task_id}",
        text=review,
        metadata={"agent": "ingrid", "type": "sprint10_close_review"},
    )
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/sprint10_close_review", "result": result},
    )

    print(f"[{NAME}]\n\n{review}")
    print(f"\n\n--- reviews row written: result='{result}' for sprint_id {sprint_id} ---")


if __name__ == "__main__":
    run()
