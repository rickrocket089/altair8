"""Entry point for Kenji's Sprint 3 deep-dive: Genially, the closest existing
analog to Altair8's goal (flagged for immediate follow-up by Ingrid in the
Sprint 2 landscape-scan review).
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

SPRINT_QUESTION = (
    "Genially was flagged as the closest existing analog to what Altair8 is trying "
    "to build. Exactly how far does it get toward AI-reasoned, non-linear "
    "communication structure, and precisely where does it stop?"
)

MODEL = "claude-sonnet-4-6"
TOOLS = [{"type": "web_search_20260209", "name": "web_search"}]


def _extract_text(content) -> str:
    return "\n".join(block.text for block in content if block.type == "text")


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 3: Genially deep-dive",
        description=SPRINT_QUESTION,
    )

    prior_scan = db.get_memory("kenji", "last_landscape_scan") or "(no prior scan found)"

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    user_message = {
        "role": "user",
        "content": (
            f"Sprint question: {SPRINT_QUESTION}\n\n"
            "For context, here is your own Sprint 2 landscape scan, where you first "
            "flagged Genially for follow-up:\n\n"
            f"{prior_scan}\n\n"
            "Now go deep on Genially specifically, using web search (docs, "
            "product pages, demos, reviews, changelogs). Cover:\n"
            "1. What Genially actually generates and how (interactivity model, "
            "authoring flow, what is AI-driven vs. manually authored).\n"
            "2. Whether it does any real reasoning about communication structure "
            "(sequencing, branching, non-linear navigation) or whether "
            "'interactive' just means clickable hotspots on a fundamentally "
            "linear deck.\n"
            "3. Its orchestration/pipeline approach if visible (does it use an "
            "LLM to decide structure, or is structure entirely template-driven?).\n"
            "4. A clear verdict: where exactly does it stop short of Altair8's "
            "goal (agents reasoning about *why* a visual form communicates "
            "better, then building it)? Ground this in what you found, not "
            "speculation.\n"
            "End with a 'IMPLICATIONS FOR ALTAIR8' section: concrete patterns "
            "worth reusing vs. concrete gaps our framework-analysis step "
            "(AI-Scientist-v2 / RISE) should try to fill."
        ),
    }
    messages = [user_message]

    response = client.messages.create(
        model=MODEL, max_tokens=8000, system=SYSTEM_PROMPT, tools=TOOLS, messages=messages
    )
    total_input = response.usage.input_tokens
    total_output = response.usage.output_tokens

    while response.stop_reason == "pause_turn":
        messages = [user_message, {"role": "assistant", "content": response.content}]
        response = client.messages.create(
            model=MODEL, max_tokens=8000, system=SYSTEM_PROMPT, tools=TOOLS, messages=messages
        )
        total_input += response.usage.input_tokens
        total_output += response.usage.output_tokens

    report = _extract_text(response.content)
    db.log_usage("kenji", total_input, total_output)

    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"genially-deep-dive-task-{task_id}",
        text=report,
        metadata={"agent": "kenji", "type": "genially_deep_dive"},
    )
    db.set_memory("kenji", "genially_deep_dive", report)
    db.update_task(
        task_id, status="completed", result=report,
        artifact_type="research_brief", artifact_payload={"memory_key": "kenji/genially_deep_dive"},
    )

    print(f"[{NAME}] Genially deep-dive complete.\n\n{report}")


if __name__ == "__main__":
    run()
