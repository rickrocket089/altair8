"""Ingrid reviews the Gemini addition to Sprint 6's behavioral reasoning
test. This is treated as a real content review, not a spot-check -- unlike
the earlier text-only revision (60/40 estimate removed, provisional
annotations added), this adds genuinely new data (a third model) and new
analysis, so it needs the same rigor as the original Sprint 6 review.
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
        title="Review: Sprint 6 Gemini addition",
        description="Real content review of the 3-model update to the behavioral reasoning test -- not a text-only revision.",
    )

    brief = db.get_memory("naledi", "behavioral_reasoning_test") or "(no brief found)"
    pre_gemini = db.get_memory("naledi", "behavioral_reasoning_test_pre_gemini") or "(not found)"

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Naledi has added Gemini as a third model to Sprint 6's "
                    "behavioral reasoning test (closing a gap flagged in the "
                    "original 2-model pilot, once a Google API key became "
                    "available). This is a real update with new data and new "
                    "analysis, not a wording fix -- review it with full "
                    "rigor, same as the original Sprint 6 review.\n\n"
                    "Specific things to check:\n\n"
                    "1. Proofreading/editing quality -- read the full brief "
                    "carefully for any leftover drafting artifacts (e.g. a "
                    "self-correction left visible in the text instead of "
                    "cleaned up).\n\n"
                    "2. Are the new per-model 'failure mode' labels (medium-"
                    "frame anchoring for GPT, form-conservatism for Gemini, "
                    "over-trust-in-convention for Claude) actually "
                    "well-supported by the quoted evidence, or do they "
                    "overstate what 6 data points per model can show?\n\n"
                    "3. Does adding a third model correctly keep the "
                    "provisional/single-run framing (S6/no false-precision "
                    "confidence numbers), or has any of that discipline "
                    "eroded now that the picture feels richer?\n\n"
                    "4. Is it honestly disclosed that this was a two-step "
                    "process (Claude+GPT first, Gemini added later), or does "
                    "the brief read as if all three were tested together "
                    "from the start?\n\n"
                    "5. Does the revised Sprint 7 adversarial-pairs section "
                    "make sense now that it spans 3 models, or does it "
                    "overreach (e.g. assuming failure modes found on 2 "
                    "variants will replicate at scale)?\n\n"
                    f"UPDATED BRIEF (3 models):\n\n{brief}\n\n"
                    f"FOR REFERENCE, THE PRIOR 2-MODEL VERSION:\n\n{pre_gemini}\n\n"
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
        metadata={"agent": "ingrid", "type": "sprint6_gemini_addition_review"},
    )
    db.set_memory("ingrid", "sprint6_gemini_addition_review", review)
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review", artifact_payload={"memory_key": "ingrid/sprint6_gemini_addition_review"},
    )

    print(f"[{NAME}]\n\n{review}")


if __name__ == "__main__":
    run()
