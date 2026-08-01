"""Entry point for the Team Leader agent (Sophie Marchetti).

Bootstraps the plumbing end-to-end: confirms the Postgres and Chroma
connections, records a status entry, and asks Sophie for one real
greeting/status message via Claude to prove the persona + memory wiring
works before other agent roles are built out.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.team_leader.persona import NAME, SYSTEM_PROMPT
from tools import db
from tools import vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))


def bootstrap() -> None:
    db.set_memory("team_leader", "status", "online")
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="team_leader",
        title="Bootstrap check",
        description="Verify Postgres + Chroma + Claude wiring end-to-end.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Give a short status update introducing yourself to the founder, "
                    "confirming the team infrastructure is online, and stating the "
                    "single next step you recommend for Altair8."
                ),
            }
        ],
    )
    greeting = response.content[0].text
    db.log_usage("team_leader", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="team_leader_memory",
        doc_id=f"bootstrap-task-{task_id}",
        text=greeting,
        metadata={"agent": "team_leader", "type": "bootstrap"},
    )
    db.set_memory("team_leader", "last_greeting", greeting)
    db.update_task(task_id, status="completed", result="Infra verified.")

    print(f"[{NAME}] {greeting}")


if __name__ == "__main__":
    bootstrap()
