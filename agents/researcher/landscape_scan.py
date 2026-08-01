"""Entry point for Kenji's landscape-scan sprint: survey existing AI-generated
slide/visualization tools and where they hit the ceiling, using web search.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

SPRINT_QUESTION = (
    "What does the current landscape of AI-generated slide/visualization tools "
    "look like, and where do they visibly hit the ceiling we're trying to get past?"
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
        title="Landscape scan: existing AI slide/visualization tools",
        description=SPRINT_QUESTION,
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    user_message = {
        "role": "user",
        "content": (
            f"Sprint question: {SPRINT_QUESTION}\n\n"
            "Use web search to identify the top 20 AI-generated slide/presentation/"
            "visualization tools on the market today (e.g. Gamma, Tome, Beautiful.ai, "
            "Copilot in PowerPoint, Canva's AI tools, and others you find). "
            "Go for breadth, not depth: for each tool give (1) name, (2) what it "
            "does and how it generates output, (3) one paragraph on where it "
            "visibly hits a ceiling — falls back to a static slide-shaped box, "
            "can't handle non-linear or complex communication, etc. "
            "If any tool looks like it may have already solved what our team is "
            "trying to build, flag it explicitly and clearly at the end under a "
            "'FLAG FOR FOLLOW-UP' heading — don't go deep on it now, just flag it."
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
        doc_id=f"landscape-scan-task-{task_id}",
        text=report,
        metadata={"agent": "kenji", "type": "landscape_scan"},
    )
    db.set_memory("kenji", "last_landscape_scan", report)
    db.update_task(
        task_id, status="completed", result=report,
        artifact_type="research_brief", artifact_payload={"memory_key": "kenji/last_landscape_scan"},
    )

    print(f"[{NAME}] Landscape scan complete.\n\n{report}")


if __name__ == "__main__":
    run()
