"""Entry point for Ingrid to critically review Kenji's landscape scan."""
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
        title="Review: Kenji's AI slide/visualization landscape scan",
        description="Critically review the 20-tool landscape scan before it feeds the next sprint.",
    )

    landscape_scan = db.get_memory("kenji", "last_landscape_scan") or "(no scan found)"

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Kenji's landscape scan of 20 AI slide/visualization tools:\n\n"
                    f"{landscape_scan}\n\n"
                    "Critically review this. Kenji could only research from public "
                    "material (docs, marketing pages, reviews) — flag anywhere a "
                    "'ceiling' claim reads as speculation rather than something "
                    "actually sourced. Check the cross-cutting synthesis: is it "
                    "actually supported by the 20 individual entries, or does it "
                    "overreach? Scrutinize the three 'FLAG FOR FOLLOW-UP' items "
                    "specifically — are they justified, or is any of them actually "
                    "closer to solving our problem than the report gives credit for "
                    "(or further away than claimed)? End with specific, actionable "
                    "revision instructions Kenji can apply directly — not just "
                    "general critique. Keep the per-tool speculation-flagging tight "
                    "(a sentence or two per issue, not a subsection each) so you have "
                    "room to fully cover the synthesis, the flag items, and the "
                    "revision instructions within this response."
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
        metadata={"agent": "ingrid", "type": "landscape_scan_review"},
    )
    db.set_memory("ingrid", "landscape_scan_review", review)
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review", artifact_payload={"memory_key": "ingrid/landscape_scan_review"},
    )

    print(f"[{NAME}]\n\n{review}")


if __name__ == "__main__":
    run()
