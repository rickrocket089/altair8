"""Ingrid's second pass on Sprint 11: are Blocks A, B and C actually fixed?

Her close review returned NEEDS_REVISION with three named blocks and an explicit
condition: "Once fixed, Sophie should run a second render verification
confirming all three, and the sprint outcome text must be written as specified
in Section 4 above." This is the pass that decides whether that happened.

She gets her own review verbatim, the second render verification, and the actual
diff -- not a summary of the diff. Sprint 8's lesson was that a gate which reads
an account of a change rather than the change itself is not a gate.

Two things are put to her that she did not ask about, because they are things a
reviewer should be told rather than left to discover:

1. Her close review reported Kenji's prior-art brief as "ending mid-sentence"
   and logged it as a process gap. It does not. The brief is complete in the
   database; the close-review script truncated it at 16000 characters before
   showing it to her, and Priya's answers at 24000. That was Sophie's error, it
   changed what Ingrid saw, and it is corrected here rather than left standing
   in the research record.

2. Mateo's spec contradicts itself on the failure state: it says to display the
   root alone, and the banner text it prescribes says "Showing full map."
   Ingrid's review resolved it one way ("root alone, marked, with a banner, not
   the full map") and the build follows her, not the spec. She should rule on
   that explicitly rather than have the ambiguity quietly settled by whoever
   happened to write the code.

This pass writes a reviews row: log_sprint.py needs an 'approved' one before
Sprint 11 can close, and the close review's row is 'needs_revision'.
"""
import os
import subprocess

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

SPRINT_NUMBER = 11
REPO = os.path.join(os.path.dirname(__file__), "..", "..")


def _diff() -> str:
    """The actual change, from git, not an account of it."""
    try:
        return subprocess.run(
            ["git", "diff", "--", "prototype/commitment_audit/"],
            cwd=REPO, capture_output=True, text=True, timeout=60,
        ).stdout
    except Exception as exc:  # pragma: no cover - diagnostic path
        return f"(diff unavailable: {exc})"


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")
    sprint_id = db.get_sprint_id(SPRINT_NUMBER)

    prior_review = db.get_memory("ingrid", "sprint11_close_review") or "(missing)"
    verification = db.get_memory("team_leader", "sprint11_render_verification") or "(missing)"
    diff = _diff()

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Confirm: Sprint 11 Blocks A, B, C",
        description="Second pass. The sprint cannot close without an approved verdict.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Second pass on Sprint 11. You returned NEEDS_REVISION on three "
            "blocks. Below is your own review verbatim, the second render "
            "verification you required, and the actual diff of the fixes. "
            "Decide whether the sprint may now close.\n\n"
            "Check each block against the diff and the verification, in that "
            "order -- the diff is what was done, the verification is what it "
            "looks like. If a block is only partially fixed, say so and hold "
            "the close; you have held it once already and nothing about that "
            "was wrong.\n\n"
            "TWO THINGS YOU SHOULD KNOW BEFORE YOU RULE:\n\n"
            "(1) A CORRECTION TO YOUR OWN REVIEW. In Section 5 you reported "
            "that Kenji's prior-art brief 'ended with a mid-sentence "
            "truncation' and recorded it as a process gap that nobody flagged. "
            "That is not true of the brief. The brief in the database is "
            "complete and ends with a proper sign-off. The close-review script "
            "sliced it to 16000 characters before showing it to you -- the cut "
            "landed exactly at 'What C1 may c—' -- and it also cut 289 "
            "characters from the end of Priya's answers. Sophie wrote that "
            "script; the defect is hers, not Kenji's and not the process's. "
            "The slices are removed now. You reviewed gate #1 on a document "
            "missing its last 537 characters. Say whether that changes any of "
            "your Section 5 conclusions, and strike the process-gap finding if "
            "it should be struck. Do not soften this for Sophie's benefit.\n\n"
            "(2) A CONTRADICTION IN THE SPEC YOU ENFORCED. Mateo's spec, Case "
            "1, says: 'Do not render a PRP. Display the root node alone, "
            "visually marked as below confidence threshold. Show a banner: "
            "\"No path above confidence threshold tau. Showing full map. Lower "
            "the threshold to see a reading path.\"' The instruction says root "
            "alone; the banner text it dictates says the full map is being "
            "shown. These cannot both hold. Your review resolved it as 'root "
            "alone, marked, with a banner, not the full map', and the build "
            "followed you rather than the spec. Rule on this explicitly: is "
            "root-alone right, or should the failure state show the full map "
            "under a loud banner? If you now think the spec's banner text was "
            "the true intent, say so and treat Block C as not yet met. Either "
            "way the resolution belongs in the record, because the next person "
            "to read that spec will hit the same contradiction.\n\n"
            "Also judge, briefly: the failure state currently still shows the "
            "category filters and 'Expand everything' although one node is "
            "drawn. Carried, or fix now?\n\n"
            "Then give the verdict. If you approve, Sprint 11 closes with the "
            "outcome text Sophie will write to your Section 4 specification, "
            "backlog #13, #21 and #22 closed, and your new items added.\n\n"
            f"=== YOUR CLOSE REVIEW (verbatim) ===\n{prior_review}\n\n"
            f"=== SECOND RENDER VERIFICATION ===\n{verification}\n\n"
            f"=== THE DIFF ===\n{diff}\n\n"
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
        result=result, notes={"memory_key": "ingrid/sprint11_close_confirmation"},
    )
    db.set_memory("ingrid", "sprint11_close_confirmation", review)
    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"review-task-{task_id}",
        text=review,
        metadata={"agent": "ingrid", "type": "sprint11_close_confirmation"},
    )
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/sprint11_close_confirmation", "result": result},
    )

    print(f"[{NAME}]\n\n{review}")
    print(f"\n\n--- reviews row written: result='{result}' for sprint_id {sprint_id} ---")


if __name__ == "__main__":
    run()
