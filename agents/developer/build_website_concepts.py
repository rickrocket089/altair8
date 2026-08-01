"""Entry point for Mateo to build 3 distinct external-facing website concepts
for Altair8, showing the mission, the team, how the team works, and progress
highlights. Each concept is a genuinely different visual direction, not a
palette swap — the founder picks one afterward.
"""
import os
import re

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.developer.persona import NAME, SYSTEM_PROMPT
from agents.permissions import require_tool
from tools import db
from tools.team import TEAM

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "workspace", "outputs")

CONCEPTS = [
    {
        "slug": "site-concept-1-editorial",
        "direction": (
            "EDITORIAL / NARRATIVE. Warm off-white or cream background, serif "
            "display type for headlines, long-form single-page scroll that reads "
            "like a research lab's public manifesto. Should feel written by "
            "people who think carefully, not a SaaS landing page. Generous "
            "whitespace, pull-quotes for the North Star."
        ),
    },
]


def build_context() -> str:
    north_star = db.get_memory("team_leader", "north_star") or "(not set)"
    sprints = db.list_sprints()
    papers = db.paper_count()

    team_text = "\n".join(
        f"- {m['name']} — {m['role']} ({m['origin']}): {m['blurb']}" for m in TEAM
    )
    sprints_text = "\n".join(
        f"- Sprint {s['sprint_number']} [{s['status']}]: \"{s['question']}\"\n  Outcome: {s['outcome']}"
        for s in sprints
    ) or "(no sprints logged yet)"

    return (
        f"NORTH STAR:\n{north_star}\n\n"
        f"TEAM:\n{team_text}\n\n"
        f"SPRINT HISTORY ({len(sprints)} sprints, {papers} papers analyzed so far):\n{sprints_text}\n\n"
        "HOW THE TEAM WORKS: an AI-only agent team (Team Leader, two Researchers, "
        "a Developer, a Reviewer) running in 2-day-max sprints. Each sprint has one "
        "focused question; the Team Leader plans it with the founder, the "
        "Researchers/Developer produce work, the Reviewer critically checks it "
        "before anything is presented as final."
    )


def run() -> None:
    require_tool("mateo", "write_prototype_file")
    db.set_memory("mateo", "status", "online")
    context = build_context()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    written = []

    for concept in CONCEPTS:
        task_id = db.create_task(
            created_by="team_leader",
            assigned_to="mateo",
            title=f"External website concept: {concept['slug']}",
            description=concept["direction"],
        )

        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Build ONE self-contained external-facing website for Altair8 "
                        f"(inline CSS/JS, no external dependencies, one HTML file). "
                        f"Sections required: mission/North Star, the team (all 5, with "
                        f"roles), how we work (the sprint process), and a progress "
                        f"highlights section (papers analyzed, sprints completed with "
                        f"a one-line outcome each — this is a public summary, not the "
                        f"internal ops dashboard, so no token-cost figures here).\n\n"
                        f"Visual direction for THIS concept: {concept['direction']}\n\n"
                        f"Content to use:\n\n{context}\n\n"
                        "Output ONLY the complete HTML in a single ```html fenced code "
                        "block, closed with a trailing ```. No explanation text before "
                        "or after — just the code block."
                    ),
                }
            ],
        ) as stream:
            response = stream.get_final_message()
        text = response.content[0].text
        db.log_usage("mateo", response.usage.input_tokens, response.usage.output_tokens)

        match = re.search(r"```html\n(.*?)```", text, re.DOTALL)
        if match:
            html = match.group(1).strip()
        else:
            open_fence = re.search(r"```html\n", text)
            html = text[open_fence.end():].strip() if open_fence else text.strip()

        out_path = os.path.join(OUTPUT_DIR, f"{concept['slug']}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        written.append(out_path)

        db.update_task(task_id, status="completed", result=f"Written to {out_path}")
        print(f"[{NAME}] Wrote {concept['slug']}.html")

    print(f"\n[{NAME}] All 3 concepts written:\n" + "\n".join(written))


if __name__ == "__main__":
    run()
