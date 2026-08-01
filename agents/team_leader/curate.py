"""Sprint curation entrypoint for the Team Leader agent (Sophie Marchetti).

Reads the team's latest outputs (briefs, prototype notes, review) plus open
tasks, and asks Sophie to curate a founder-readable summary: key findings
and what the team is currently working on. Feeds the dashboard.
"""
import os
import re

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.team_leader.persona import NAME, SYSTEM_PROMPT
from tools import db

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))


def curate() -> None:
    sprints = db.list_sprints()
    sprints_text = "\n\n".join(
        f"Sprint {s['sprint_number']} [{s['status']}]: \"{s['question']}\"\nOutcome: {s['outcome']}"
        for s in sprints
    ) or "(no sprints logged yet)"

    open_tasks = db.list_open_tasks()
    open_tasks_text = "\n".join(f"- [{t['assigned_to']}] {t['title']}" for t in open_tasks) or "(none)"

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Full sprint history, most recent last:\n\n{sprints_text}\n\n"
                    f"Open/in-progress tasks:\n{open_tasks_text}\n\n"
                    "Curate this for the founder's dashboard. Weight the MOST RECENT "
                    "sprint heaviest — that's what's actually current — and only pull "
                    "in older sprints if they're still load-bearing context. Output "
                    "EXACTLY two sections using these literal markers:\n"
                    "===FINDINGS===\n"
                    "(3-6 bullet points, each one sentence, the most important things "
                    "the team has actually learned or built so far — not a recap of "
                    "every detail, and be honest about caveats raised during review)\n"
                    "===CURRENT===\n"
                    "(1-2 sentences on what the team is working on right now — based on "
                    "open tasks and whether the latest sprint is actually closed)"
                ),
            }
        ],
    )
    text = response.content[0].text
    db.log_usage("team_leader", response.usage.input_tokens, response.usage.output_tokens)

    findings_match = re.search(r"===FINDINGS===\s*(.*?)\s*===CURRENT===", text, re.DOTALL)
    current_match = re.search(r"===CURRENT===\s*(.*)", text, re.DOTALL)
    findings = findings_match.group(1).strip() if findings_match else text
    current = current_match.group(1).strip() if current_match else ""

    db.set_memory("team_leader", "curated_findings", findings)
    db.set_memory("team_leader", "current_focus", current)

    print(f"[{NAME}] Curated findings:\n\n{findings}\n\nCurrently working on:\n{current}")


if __name__ == "__main__":
    curate()
