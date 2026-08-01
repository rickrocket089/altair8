"""Local dashboard for the Altair8 team: KPI tiles, curated findings, and
what the team is currently working on. Reads directly from Postgres."""
import os

from dotenv import load_dotenv
from flask import Flask, render_template

from tools import db
from tools.team import TEAM

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

app = Flask(__name__)


def compact_number(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


@app.route("/")
def index():
    usage = db.total_usage()
    total_tokens = usage["input_tokens"] + usage["output_tokens"]

    findings_raw = db.get_memory("team_leader", "curated_findings") or ""
    findings = [
        line.lstrip("- ").strip()
        for line in findings_raw.splitlines()
        if line.strip().startswith("-")
    ]
    current_focus = db.get_memory("team_leader", "current_focus") or "No sprint in progress."

    open_tasks = db.list_open_tasks()
    sprints = list(reversed(db.list_sprints()))

    return render_template(
        "index.html",
        papers=compact_number(db.paper_count()),
        tokens=compact_number(total_tokens),
        tasks_open=len(open_tasks),
        findings=findings,
        current_focus=current_focus,
        open_tasks=open_tasks,
        sprints=sprints,
        team=TEAM,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
