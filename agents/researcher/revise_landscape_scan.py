"""Entry point for Kenji to revise the landscape scan per Ingrid's review.

Reads his original report + Ingrid's critique and produces a revised report
that becomes the new current version (kenji/last_landscape_scan).
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))


def run() -> None:
    require_tool("kenji", "write_brief")
    original = db.get_memory("kenji", "last_landscape_scan") or ""
    review = db.get_memory("ingrid", "landscape_scan_review") or ""

    if not original or not review:
        raise RuntimeError("Missing original report or Ingrid's review — run those first.")

    db.set_memory("kenji", "landscape_scan_v1", original)

    task_id = db.create_task(
        created_by="ingrid",
        assigned_to="kenji",
        title="Revise landscape scan per Ingrid's review",
        description="Apply Ingrid's 7 revision instructions to the landscape scan.",
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
                    f"Your original landscape scan:\n\n{original}\n\n"
                    f"Ingrid's review of it:\n\n{review}\n\n"
                    "Produce a revised version of your landscape scan that applies "
                    "her revision instructions directly — the epistemic-flagging "
                    "language changes, the Prezent sourcing caveat, the synthesis "
                    "qualifications, the Genially flag upgrade to 'recommend "
                    "immediate follow-up', the Flourish SDK addition, the Prezi "
                    "reframe, and the Flourish staleness flag. Keep everything that "
                    "wasn't flagged as-is — this is a targeted revision, not a "
                    "rewrite from scratch. Output the complete revised report."
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    revised = response.content[0].text
    db.log_usage("kenji", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"landscape-scan-revised-task-{task_id}",
        text=revised,
        metadata={"agent": "kenji", "type": "landscape_scan_revised"},
    )
    db.set_memory("kenji", "last_landscape_scan", revised)
    db.update_task(
        task_id, status="completed", result="Revision applied; see kenji/last_landscape_scan.",
        artifact_type="research_brief", artifact_payload={"memory_key": "kenji/last_landscape_scan"},
    )

    print(f"[{NAME}] Revised landscape scan (Ingrid's feedback integrated):\n\n{revised}")


if __name__ == "__main__":
    run()
