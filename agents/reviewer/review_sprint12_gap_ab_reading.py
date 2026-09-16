"""Ingrid reviews Kenji's Sprint 12 synthesis before Sophie closes the sprint.

This is a content review with one unusual property: Kenji's own honest
conclusion is that the literature CANNOT answer the sprint's leitfrage -- a
null result on 9 real full-text readings, not a retrieval failure. The
temptation this review exists to catch is the opposite of the usual one:
not "did he overclaim a finding," but "did he correctly resist the pressure
to manufacture a finding where the honest answer is negative." He also
flagged that Sophie's own DSR transition criterion may be unmeetable as
written -- that claim about her own criterion needs checking too, not just
taken at face value.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")

    brief = db.get_memory("kenji", "sprint12_gap_ab_reading") or "(missing)"
    hypotheses = db.get_memory("team_leader", "hypotheses") or "(missing)"
    sprint_id = db.get_sprint_id(12)

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Review: Sprint 12 Gap A+B synthesis (9 papers vs. hypothesis 6)",
        description="Content review before Sophie can close Sprint 12 via the hard review gate.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Kenji read 9 founder-supplied full-text papers (Gap A: argument "
            "mapping / knowledge cartography / argument mining; Gap B: NLG "
            "architecture / politeness / sentence planning) against a single "
            "leitfrage: do any discriminate 'internalized structure' from "
            "'convention reproduction' as the source of audience/goal-"
            "sensitive behavior (hypothesis 6 / backlog #23)? His conclusion "
            "across all 9: no, none do, and this is the wrong literature "
            "type for that question. No novelty flags raised against C1. "
            "Review before Sophie closes Sprint 12 on this.\n\n"
            "SPECIFIC THINGS TO CHECK:\n\n"
            "1. IS THE NULL RESULT REAL OR IS HE UNDER-READING. A negative "
            "finding across 9/9 papers is the kind of clean result that's "
            "easy to produce by asking a narrow question and not looking "
            "hard for a fit. Spot-check at least 3 of the per-paper readings "
            "against what you'd expect that paper to actually contain -- "
            "does Bangalore & Stent's individual-preference-modeling result, "
            "or the Danescu et al. sentence-position finding, or Buckingham "
            "Shum et al.'s human/XIP rhetorical-marker overlap actually "
            "support 'does not bear on this distinction' as cleanly as "
            "claimed? Or is there a more generous, still-honest reading that "
            "would count as weak/indirect evidence rather than none?\n\n"
            "2. THE NOVELTY-FLAG DISCIPLINE. Founder's instruction "
            "(2026-09-16): don't escalate ordinary contrary findings, only "
            "direct undermining of C1's mechanism. Kenji examined 3 near-"
            "candidates (van Gelder's evaluative overlay, Mayer/Cabrio/"
            "Villata's evidence-type weighting, the Wigmore/Belvedere/SEAS "
            "systems) and ruled all three categorically distinct from C1's "
            "confidence-bound-to-epistemic-category mechanism. Are those "
            "distinctions actually sound, or is 'categorically distinct' "
            "doing some work that a closer look would complicate?\n\n"
            "3. THE CLAIM ABOUT SOPHIE'S OWN CRITERION. Kenji states that "
            "Sophie's DSR transition criterion (b) -- 'the H6 leitfrage has "
            "a clear direction' -- may be unmeetable as written if she meant "
            "'literature points toward an answer,' and proposes she should "
            "instead accept 'direction = run the behavioral test' as "
            "satisfying it. Is this a fair reading of what a null result "
            "means for a stated closure criterion, or is Kenji redefining "
            "the criterion to fit what he found rather than flagging a "
            "genuine mismatch for Sophie to decide?\n\n"
            "4. THE DESIGN NOTE FOR BACKLOG #23. He recommends #23 include "
            "novel-context conditions based on the Bangalore/Stent and "
            "Danescu findings. Does that recommendation actually follow from "
            "those two findings, or is it generically good experimental "
            "design advice being retrofitted with citations?\n\n"
            "5. SCOPE HONESTY. All 9 close-reads report zero connector "
            "queries (supplied documents only). Correct call for this task "
            "-- confirm you agree, or flag if a corpus cross-check should "
            "have happened anywhere.\n\n"
            "End with a clear recommendation to Sophie: approved, revise "
            "(name exactly what), or the sprint's own premise needs "
            "rethinking. This feeds directly into whether Sprint 12 closes "
            "and whether Backlog #23 gets scoped the way Kenji suggests.\n\n"
            f"=== KENJI'S SPRINT 12 BRIEF ===\n{brief}\n\n"
            f"=== CURRENT HYPOTHESES, FOR CONTEXT ===\n{hypotheses}\n"
        )}],
    ) as stream:
        response = stream.get_final_message()

    review = response.content[0].text
    db.log_usage("ingrid", response.usage.input_tokens, response.usage.output_tokens)

    # The `reviews` table row that actually gates log_sprint.py is written
    # separately, deliberately, once a human (or the orchestrating session)
    # has read this text -- not auto-parsed from free-form review prose here.

    db.set_memory("ingrid", "sprint12_gap_ab_review", review)
    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"review-task-{task_id}",
        text=review,
        metadata={"agent": "ingrid", "type": "sprint12_gap_ab_review"},
    )
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/sprint12_gap_ab_review", "sprint_id": sprint_id},
    )

    print(f"[{NAME}]\n\n{review}")
    print(f"\n\n--- {len(review)} chars, stored as ingrid/sprint12_gap_ab_review (sprint_id={sprint_id}) ---")


if __name__ == "__main__":
    run()
