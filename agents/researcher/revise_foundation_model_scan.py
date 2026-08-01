"""Entry point for Kenji to revise the foundation-model capability scan per
Ingrid's Sprint 4 review. Reads his original brief + Ingrid's critique and
produces a revised version that becomes the new current version
(kenji/foundation_model_capabilities_scan).
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
    original = db.get_memory("kenji", "foundation_model_capabilities_scan") or ""
    review = db.get_memory("ingrid", "sprint4_review") or ""

    if not original or not review:
        raise RuntimeError("Missing original brief or Ingrid's review — run those first.")

    db.set_memory("kenji", "foundation_model_capabilities_scan_v1", original)

    task_id = db.create_task(
        created_by="ingrid",
        assigned_to="kenji",
        title="Revise foundation-model capability scan per Ingrid's Sprint 4 review",
        description="Apply Ingrid's 3 revision instructions for Deliverable 1.",
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
                    f"Your original brief:\n\n{original}\n\n"
                    f"Ingrid's full Sprint 4 review (your part is "
                    f"'DELIVERABLE 1'):\n\n{review}\n\n"
                    "Apply her 3 revision instructions for Deliverable 1 "
                    "specifically:\n"
                    "1. Add an explicit caveat in the OpenAI and Google "
                    "sections: this scan covers documented first-party "
                    "capabilities, not implicit model behavior -- base "
                    "models may have internalized form-selection heuristics "
                    "not visible in product documentation. This is a scope "
                    "limitation, not a finding.\n"
                    "2. Flag the Microsoft/OpenAI chart-suggestion comparison "
                    "as a cross-tier comparison (independent practitioner "
                    "review vs. official documentation) and downgrade the "
                    "implied confidence that Microsoft is 'more developed' "
                    "on that dimension.\n"
                    "3. Add a sentence to the Overall Verdict section "
                    "stating explicitly what further investigation would be "
                    "needed to address the stronger version of the research "
                    "question: behavioral testing with controlled prompts to "
                    "probe whether base models produce principled "
                    "form-selection reasoning even without documented skill "
                    "scaffolding.\n\n"
                    "These are precision corrections, not a rewrite -- keep "
                    "everything else as-is. Output the complete revised brief."
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    revised = response.content[0].text
    db.log_usage("kenji", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"foundation-model-scan-revised-task-{task_id}",
        text=revised,
        metadata={"agent": "kenji", "type": "foundation_model_capabilities_scan_revised"},
    )
    db.set_memory("kenji", "foundation_model_capabilities_scan", revised)
    db.update_task(
        task_id, status="completed",
        result="Revision applied; see kenji/foundation_model_capabilities_scan.",
        artifact_type="research_brief",
        artifact_payload={"memory_key": "kenji/foundation_model_capabilities_scan"},
    )

    print(f"[{NAME}] Revised foundation-model capability scan:\n\n{revised}")


if __name__ == "__main__":
    run()
