"""Ingrid's formal close review for Sprint 11 (the C1 Commitment Audit build).

log_sprint.py refuses to mark a sprint completed without an 'approved' row in
the reviews table. Sprint 11 has no review row of any kind -- the prototype was
built on 2026-08-20 and nothing has judged it since, while the sprint sat
'in_progress' for 26 days.

Two things make this review different from the Sprint 10 close review:

1. It has a real browser render to judge, not just source. The founder asked for
   the verification first, so Ingrid is reviewing the artifact as it actually
   appears -- the first time in this project that a prototype review has had
   that. Six defects were found; her job includes deciding which of them block.

2. It reviews a build against a spec that was itself gated. Mateo's scaffold
   spec and Kenji's prior-art check were her own two conditions from Sprint 10.
   So the question is not only "is this good" but "did the gates she imposed
   actually do any work."
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

SPRINT_NUMBER = 11
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "prototype", "commitment_audit")


def _src(name: str) -> str:
    with open(os.path.join(SRC_DIR, name), encoding="utf-8") as f:
        return f.read()


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")
    sprint_id = db.get_sprint_id(SPRINT_NUMBER)

    # Passed whole, never sliced. The first run of this review truncated
    # Kenji's brief at 16000 chars and Priya's answers at 24000, and Ingrid
    # correctly reported the brief as "ending mid-sentence" -- a defect this
    # script had introduced, not one the team committed. Slicing a gate
    # document to fit a prompt silently changes what the reviewer reviews.
    prior_art = db.get_memory("kenji", "c1_argument_visualization_check") or ""
    spec = db.get_memory("mateo", "c1_spanning_scaffold_spec") or ""
    answers = db.get_memory("priya", "c1_build_question_answers") or ""
    verification = db.get_memory("team_leader", "sprint11_render_verification") or ""

    backlog = "\n".join(
        f"  #{i['id']} [{i['priority']}] {i['title']}"
        for i in db.list_backlog_items() if i["status"] == "open"
    )

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Close review: Sprint 11 (C1 Commitment Audit build)",
        description="Formal review gate. The sprint cannot close without an approved verdict.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Formal close review for Sprint 11. log_sprint.py will not mark the "
            "sprint completed without an 'approved' verdict from you. You have "
            "blocked two closes before (Sprints 4 and 8) -- this is a real gate.\n\n"
            "SPRINT 11's QUESTION, as written in the database: 'Build the C1 "
            "Commitment Audit prototype -- an agent that audits its own claims "
            "as evidence / inference / assumption / assertion with continuous "
            "confidence, and renders an argument map where visual weight derives "
            "from confidence rather than rhetorical emphasis. Two Ingrid "
            "conditions gate the build: a targeted argument-visualization "
            "prior-art search before any external framing, and a formal "
            "specification of the minimum-spanning-argument scaffold before "
            "Mateo starts.'\n\n"
            "WHAT ACTUALLY HAPPENED: both your gates ran (Kenji's prior-art "
            "check, Mateo's spec). Priya settled five build questions. Mateo "
            "built prototype/commitment_audit/ -- deterministic, no LLM call in "
            "the render path. The audit CONTENT is hand-authored, not "
            "agent-generated; the prototype's own footer says so. Two bugs were "
            "found by building: 'structurally unavoidable' was defined globally "
            "and returned nothing (redefined locally as load-bearing), and the "
            "sample audit collapsed two test cases onto one claim so the "
            "propagation warning never fired (split into two). Then the sprint "
            "sat open and unreviewed for 26 days.\n\n"
            "Judge the following. Be direct; a diplomatic review here is worth "
            "nothing.\n\n"
            "1. THE RENDER. For the first time in this project a prototype has "
            "been verified in a real browser before review (report below, with "
            "six defects). Which of those six block the close, which are "
            "carried, and which are not actually defects? Defect 4 is the one "
            "to think hardest about: C1's premise is that visual weight derives "
            "from confidence, and in the default collapsed state -- what a "
            "reader sees first -- that encoding is nearly invisible. Is that a "
            "cosmetic issue or does it hit the concept's core claim?\n\n"
            "2. SPEC CONFORMANCE, checked against the source, not the builder's "
            "account of it. Mateo's spec required that when no path clears the "
            "threshold, the map must NOT render normally -- root alone, marked, "
            "with a banner, because 'a failed PRP is itself information'. What "
            "the build does at tau=0.8 is render the full map with one sentence "
            "changed in the intro prose. Does that meet the spec, partially "
            "meet it, or quietly not meet it?\n\n"
            "3. PRIYA'S TWO RULINGS, also checked against the source. She "
            "required (a) confidence treated as ordinal, never combined, "
            "propagated or averaged, and (b) a claim that cannot exist without "
            "its category and confidence, so the schema forecloses "
            "content-first-annotate-later. The build claims both are enforced "
            "in code rather than by convention. Are they?\n\n"
            "4. DOES THIS SPRINT ANSWER ITS OWN QUESTION? The question says 'an "
            "agent that audits its own claims'. The build tests the rendering "
            "and interaction model on hand-authored content and does not "
            "involve an agent auditing anything. Backlog #24 holds the real "
            "question. Is this a correctly-scoped first half, or is it Sprint "
            "10's criterion (b) again -- a sprint closing against a question it "
            "did not actually answer? Whatever you conclude, say what the "
            "sprint's recorded outcome text must say so the research record is "
            "honest about what was and was not established.\n\n"
            "5. DID YOUR OWN GATES DO ANY WORK? You imposed the prior-art "
            "search and the spec as conditions. Trace whether either changed "
            "the build. If a gate produced a document that the build then "
            "diverged from without anyone noticing until today, the gate did "
            "not work, and you should say so plainly.\n\n"
            "6. PROCESS. Process Review #2 added a Standing Obligations Check "
            "to Sophie's persona and gave you an instruction to verify her "
            "claims against the database rather than trust them. Since then: "
            "this sprint was never closed, backlog items #13, #21 and #22 are "
            "still 'open' although the work in them is finished, and no one "
            "noticed for 26 days until the founder returned and Sophie queried "
            "the database. Did the Review #2 fixes take? Note that Process "
            "Review #3 (covering Sprints 10-12) is due after Sprint 12, so it "
            "is not yet overdue -- do not report it as late.\n\n"
            "7. THE BACKLOG at close -- what must be added, and is anything in "
            "the current list now stale?\n\n"
            f"=== RENDER VERIFICATION (Sophie, 2026-09-15) ===\n{verification}\n\n"
            f"=== MATEO'S SCAFFOLD SPEC (your gate #2) ===\n{spec}\n\n"
            f"=== PRIYA'S FIVE BUILD-QUESTION ANSWERS ===\n{answers}\n\n"
            f"=== KENJI'S ARGUMENT-VISUALIZATION PRIOR-ART CHECK (your gate #1) "
            f"===\n{prior_art}\n\n"
            f"=== SOURCE: schema.py ===\n{_src('schema.py')}\n\n"
            f"=== SOURCE: reading_path.py ===\n{_src('reading_path.py')}\n\n"
            f"=== SOURCE: renderer.py ===\n{_src('renderer.py')}\n\n"
            f"=== SOURCE: sample_audit.py ===\n{_src('sample_audit.py')}\n\n"
            f"=== OPEN BACKLOG ===\n{backlog}\n\n"
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
        result=result, notes={"memory_key": "ingrid/sprint11_close_review"},
    )
    db.set_memory("ingrid", "sprint11_close_review", review)
    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"review-task-{task_id}",
        text=review,
        metadata={"agent": "ingrid", "type": "sprint11_close_review"},
    )
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/sprint11_close_review", "result": result},
    )

    print(f"[{NAME}]\n\n{review}")
    print(f"\n\n--- reviews row written: result='{result}' for sprint_id {sprint_id} ---")


if __name__ == "__main__":
    run()
