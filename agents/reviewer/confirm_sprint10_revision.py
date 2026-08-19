"""Ingrid confirms whether Sprint 10 proposal v2 satisfies her 7 blocking items.

Her own review required this explicitly: "The sprint should not open until
Sophie returns a revised proposal incorporating items 1-7, confirmed by me."
So this is a real confirmation pass, not the orchestrating session
spot-checking -- the design changed substantively, unlike the pure text-
precision fixes of Sprints 3-6 where a spot-check was the agreed practice.

She is given her own prior review verbatim alongside v2 so she checks against
what she actually wrote, not a paraphrase of it.
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

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Confirm: Sprint 10 proposal v2 against the 7 blocking items",
        description="Confirmation pass. Sprint cannot open without it.",
    )

    prior_review = db.get_memory("ingrid", "sprint10_design_review") or "(missing)"
    revised = db.get_memory("team_leader", "sprint10_proposal") or "(missing)"

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "You reviewed the Sprint 10 design and returned 'revise "
                    "the design first' with 7 blocking items and 5 "
                    "recommended ones. Sophie has revised. Confirm or refuse.\n\n"
                    f"YOUR OWN PRIOR REVIEW, VERBATIM:\n\n{prior_review}\n\n"
                    "=====================================================\n\n"
                    f"SOPHIE'S REVISED PROPOSAL (v2):\n\n{revised}\n\n"
                    "=====================================================\n\n"
                    "Your task:\n\n"
                    "1. For EACH of your 7 blocking items, state whether v2 "
                    "satisfies it: SATISFIED / PARTIALLY SATISFIED / NOT "
                    "SATISFIED, with the specific text in v2 you are judging "
                    "against. Do not accept a change that merely mentions "
                    "your item without implementing it.\n\n"
                    "2. Your recommended items 8, 9 and 10 were deliberately "
                    "NOT applied — the founder authorised only the 7 blocking "
                    "items. Say whether you accept that, or whether any of "
                    "the three has become blocking in light of the other "
                    "changes.\n\n"
                    "3. Check whether the revision introduced any NEW problem "
                    "that did not exist in v1. Revisions commonly do. Pay "
                    "particular attention to the new Pass 4 synthesis step "
                    "and the new goal-space text — are they specified well "
                    "enough to be enforceable, or have they added surface "
                    "that looks rigorous without constraining anything?\n\n"
                    "4. Section 11 of v2 records a finding about YOU: your "
                    "prior review asserted you had cross-checked the "
                    "process-review count via tools/db.py directly. You had "
                    "not — the review scripts pass you text, not a database "
                    "connection. Your conclusion was correct but the "
                    "verification was rhetorical. Address this directly. Is "
                    "the persona instruction added after Process Review #2 "
                    "executable as written, and what should be done about "
                    "it? Do not be defensive; treat it as you would treat "
                    "the same finding about anyone else's work.\n\n"
                    "End with: CONFIRMED — sprint may open, or NOT CONFIRMED "
                    "— with the specific remaining blockers listed."
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()

    review = response.content[0].text
    db.log_usage("ingrid", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"review-task-{task_id}",
        text=review,
        metadata={"agent": "ingrid", "type": "sprint10_design_confirmation"},
    )
    db.set_memory("ingrid", "sprint10_design_confirmation", review)
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/sprint10_design_confirmation"},
    )

    print(f"[{NAME}]\n\n{review}")
    print(f"\n\n--- {len(review)} chars ---")


if __name__ == "__main__":
    run()
