"""Entry point for Mateo's Sprint 3 framework-pattern review: look at
AI-Scientist-v2 (SakanaAI) and RISE (bhanneke) purely for engineering/
organizational patterns worth adopting into how Altair8's own agent team
is run (orchestration, task handoff, review loops, pipelines, memory) —
explicitly NOT for research content or the visual-communication paradigm.
That's a separate thread (see Kenji's Genially deep-dive).
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.developer.persona import NAME, SYSTEM_PROMPT
from agents.permissions import require_tool
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

SPRINT_QUESTION = (
    "Looking only at how AI-Scientist-v2 and RISE are engineered as AI-agent-driven "
    "systems (not their research subject matter), which organizational and "
    "orchestration patterns should Altair8 adopt for how our own agent team runs?"
)

MODEL = "claude-sonnet-4-6"
TOOLS = [{"type": "web_search_20260209", "name": "web_search"}]


def _extract_text(content) -> str:
    return "\n".join(block.text for block in content if block.type == "text")


def run() -> None:
    require_tool("mateo", "write_task_artifact")
    db.set_memory("mateo", "status", "online")
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="mateo",
        title="Sprint 3: framework pattern review (AI-Scientist-v2 / RISE)",
        description=SPRINT_QUESTION,
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    user_message = {
        "role": "user",
        "content": (
            f"Sprint question: {SPRINT_QUESTION}\n\n"
            "Important scope constraint: this is NOT about the research questions "
            "those projects study, and NOT about Altair8's own visual-communication "
            "research thesis. Ignore both entirely. This is purely an engineering/"
            "organizational review — you are looking at how two teams of researchers "
            "who already have experience running AI agents for research built the "
            "*machinery* around their agents, so we can borrow good patterns for how "
            "our own 5-agent team (Team Leader, 2 Researchers, Developer, Reviewer) "
            "operates.\n\n"
            "Use web search on:\n"
            "1. AI-Scientist-v2 (SakanaAI, github.com/SakanaAI/AI-Scientist-v2)\n"
            "2. RISE (bhanneke) — Jupyter notebook to Reveal.js presentation pipeline\n\n"
            "For each, look specifically at (where the public repo/docs reveal it):\n"
            "- How agent roles are split and how work hands off between them\n"
            "- Any review/critique loop (does one agent check another's output "
            "before it's treated as final, and how is that structured?)\n"
            "- How state/memory persists between steps or runs\n"
            "- Pipeline/orchestration structure (sequential stages? a controller "
            "loop? retries on failure?)\n"
            "- Anything about how output artifacts are tracked or logged\n\n"
            "For each pattern you find, give a short verdict: adopt as-is, adopt "
            "adapted (and how), or skip (and why it doesn't fit our 5-agent setup). "
            "Be concrete about what would change in our actual repo structure "
            "(agents/, tools/db.py, tools/vectorstore.py, the tasks/sprints tables) "
            "if we adopted it — not abstract praise. If a repo's public material "
            "doesn't reveal enough to judge a pattern, say so rather than guessing."
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
    db.log_usage("mateo", total_input, total_output)

    vectorstore.remember(
        collection_name="developer_memory",
        doc_id=f"framework-pattern-review-task-{task_id}",
        text=report,
        metadata={"agent": "mateo", "type": "framework_pattern_review"},
    )
    db.set_memory("mateo", "framework_pattern_review", report)
    db.update_task(
        task_id, status="completed", result=report,
        artifact_type="pattern_review", artifact_payload={"memory_key": "mateo/framework_pattern_review"},
    )

    print(f"[{NAME}] Framework pattern review complete.\n\n{report}")


if __name__ == "__main__":
    run()
