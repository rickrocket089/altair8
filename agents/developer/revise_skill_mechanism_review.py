"""Entry point for Mateo to revise the skill-mechanism review per Ingrid's
Sprint 4 review. Reads his original review + Ingrid's critique and produces
a revised version that becomes the new current version
(mateo/skill_mechanism_review).
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.developer.persona import NAME, SYSTEM_PROMPT
from agents.permissions import require_tool
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))


def run() -> None:
    require_tool("mateo", "write_task_artifact")
    original = db.get_memory("mateo", "skill_mechanism_review") or ""
    review = db.get_memory("ingrid", "sprint4_review") or ""

    if not original or not review:
        raise RuntimeError("Missing original review or Ingrid's review — run those first.")

    db.set_memory("mateo", "skill_mechanism_review_v1", original)

    task_id = db.create_task(
        created_by="ingrid",
        assigned_to="mateo",
        title="Revise skill-mechanism review per Ingrid's Sprint 4 review",
        description="Apply Ingrid's 3 revision instructions for Deliverable 2.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Your original review:\n\n{original}\n\n"
                    f"Ingrid's full Sprint 4 review (your part is "
                    f"'DELIVERABLE 2'):\n\n{review}\n\n"
                    "Apply her 3 revision instructions for Deliverable 2 "
                    "specifically:\n"
                    "1. Reclassify Pattern P3's verdict from 'adopt as-is' "
                    "to 'adopt the principle; implementation requires design "
                    "work.' Specifically note: the observed validator "
                    "pattern covers a single deterministic check (colour "
                    "CVD). Extending to Altair8's full output-constraint set "
                    "requires first identifying which constraints are "
                    "deterministic (appropriate for scripts) vs. which are "
                    "judgment calls (not appropriate for scripts) -- "
                    "document that boundary before shipping.\n"
                    "2. Provide an explicit basis for the '~8-10 "
                    "capabilities' implementation threshold in Pattern P4. "
                    "Since this is your own judgment, not a finding from the "
                    "source material, say so explicitly and explain your "
                    "reasoning rather than presenting it as a documented "
                    "fact.\n"
                    "3. Add a note to Pattern P5 that there is design work "
                    "required before this pattern is usable -- specifically "
                    "the function-tool wrapping interface needs to be "
                    "specified. 'Ship when needed' currently implies it's "
                    "ready to ship; it isn't.\n\n"
                    "These are precision corrections, not a rewrite -- keep "
                    "everything else as-is, including the rest of the "
                    "pattern table and priority order. Output the complete "
                    "revised review."
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    revised = response.content[0].text
    db.log_usage("mateo", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="developer_memory",
        doc_id=f"skill-mechanism-review-revised-task-{task_id}",
        text=revised,
        metadata={"agent": "mateo", "type": "skill_mechanism_review_revised"},
    )
    db.set_memory("mateo", "skill_mechanism_review", revised)
    db.update_task(
        task_id, status="completed",
        result="Revision applied; see mateo/skill_mechanism_review.",
        artifact_type="pattern_review",
        artifact_payload={"memory_key": "mateo/skill_mechanism_review"},
    )

    print(f"[{NAME}] Revised skill mechanism review:\n\n{revised}")


if __name__ == "__main__":
    run()
