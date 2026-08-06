"""Ingrid reviews Sprint 7's adversarial-pairs test -- the research track
that replaces Sprint 6's flawed form-prediction probe. Real content review,
same rigor as every substantive Sprint 6 review pass, not a spot-check.
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
        title="Review: Sprint 7 adversarial-pairs test",
        description="Real content review of the adversarial-pairs design and Naledi's analysis.",
    )

    brief = db.get_memory("naledi", "adversarial_pairs_test") or "(no brief found)"

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Sprint 7's research track: an adversarial-pairs "
                    "behavioral test replacing Sprint 6's flawed form-"
                    "prediction probe (your own fix from the Sprint 6 "
                    "review). 6 pairs, 12 variants, 3 models (Claude, GPT, "
                    "Gemini). Full rigor review, same as Sprint 6.\n\n"
                    "You flagged a meta-concern at the end of Sprint 6: who "
                    "validates that adversarial-pair scenarios actually meet "
                    "the non-canonical condition? Each pair in this brief "
                    "documents an explicit canonical-form rationale and "
                    "override mechanism -- assess whether that documentation "
                    "actually holds up, pair by pair, not just whether it "
                    "exists.\n\n"
                    "Specific things to check:\n\n"
                    "1. Construction validity: for each of the 6 pairs, is "
                    "the claimed 'canonical form' genuinely the standard, "
                    "uncontroversial choice, or is it arguable? (I already "
                    "noticed one candidate issue myself: AP2-normal expected "
                    "a bar chart, but GPT chose a box plot -- which is also "
                    "defensible for comparing distributions across agents. "
                    "Check whether this means AP2's canonical-form claim was "
                    "underspecified, and look for other cases like it.)\n\n"
                    "2. Naledi flags her own major methodological concern: "
                    "the 'culturally-scripted-scenario problem' -- that the "
                    "adversarial audience/goal combinations (coaching "
                    "conversation, finance audit, VP status check, etc.) may "
                    "be recognizable professional scripts that let models "
                    "pattern-match on genre rather than genuinely reason "
                    "from audience/goal. Is this a real problem with THIS "
                    "brief's findings, or a fair caveat for future rounds? "
                    "Does it undermine the current conclusions or just "
                    "bound them?\n\n"
                    "3. Check the three-part scoring criterion (canonical "
                    "vs. non-canonical form chosen; if non-canonical, does "
                    "the reasoning explicitly name the override) was applied "
                    "consistently across all 18 model-variant combinations, "
                    "not just asserted.\n\n"
                    "4. Does the comparison back to Sprint 6's three "
                    "candidate patterns (medium-frame anchoring/GPT, "
                    "form-conservatism/Gemini, no clear failure mode/Claude) "
                    "overclaim replication, or is the 'partially replicates, "
                    "more nuanced' framing appropriately hedged?\n\n"
                    "5. Read the final two direct-answer sections carefully "
                    "-- do they stay within what 12 variants at 1 run each "
                    "can actually support?\n\n"
                    f"FULL BRIEF:\n\n{brief}\n\n"
                    "End with a recommendation: proceed, revise, or block."
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
        metadata={"agent": "ingrid", "type": "sprint7_adversarial_pairs_review"},
    )
    db.set_memory("ingrid", "sprint7_adversarial_pairs_review", review)
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review", artifact_payload={"memory_key": "ingrid/sprint7_adversarial_pairs_review"},
    )

    print(f"[{NAME}]\n\n{review}")


if __name__ == "__main__":
    run()
