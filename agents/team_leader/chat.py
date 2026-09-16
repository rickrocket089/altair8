"""Interactive chat with Sophie Marchetti (Team Leader).

Every prior team_leader script is a one-shot, single-purpose call (propose a
sprint, log a decision, ...). This is the first genuine back-and-forth: the
founder can talk to Sophie directly instead of only receiving reports.

Each turn is invoked as a fresh process (`python -m agents.team_leader.chat
"<message>"`). Conversation history persists in
`workspace/memory/team_leader_chat.json` (gitignored, same tier as other
runtime state) so the thread survives across turns without needing a long-
running process. Before every reply, Sophie is fed a live snapshot of
current_focus, hypotheses, design principles, and open backlog/candidate
counts pulled fresh from Postgres -- so she reports the real database state
instead of whatever she last said in a prior session (the exact gap her own
`__main__.py` bootstrap greeting flagged: "I cannot confirm database state
without running those checks for real").
"""
import json
import os
import sys

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.team_leader.persona import NAME, SYSTEM_PROMPT
from agents.permissions import require_tool
from tools import db

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"
HISTORY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "workspace", "memory", "team_leader_chat.json"
)


def _load_history() -> list[dict]:
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_history(history: list[dict]) -> None:
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def _live_state_block() -> str:
    require_tool("team_leader", "read_all")

    current_focus = db.get_memory("team_leader", "current_focus") or "(not set)"
    hypotheses = db.get_memory("team_leader", "hypotheses") or "(not set)"
    design_principles = db.get_memory("team_leader", "design_principles") or "(not set)"
    north_star = db.get_memory("team_leader", "north_star") or "(not set)"

    backlog = db.list_backlog_items(status="open")
    candidates = db.list_candidate_approaches(status="open")
    sprints = db.list_sprints()
    reviews = db.list_process_reviews()

    last_sprint = sprints[-1] if sprints else None
    last_review = reviews[-1] if reviews else None

    backlog_lines = "\n".join(
        f"  #{b['id']} [{b['priority']}] {b['title']}" for b in backlog
    ) or "  (none open)"
    candidate_lines = "\n".join(
        f"  #{c['id']} [{c['priority']}] {c['title']}" for c in candidates
    ) or "  (none open)"
    last_review_line = (
        f"covers sprints {last_review['covers_sprint_from']}-{last_review['covers_sprint_to']}"
        if last_review else "none"
    )

    return f"""CURRENT LIVE STATE (queried fresh from Postgres just now -- this is ground
truth, not memory; if it conflicts with anything you recall saying earlier,
this wins):

NORTH STAR:
{north_star}

CURRENT FOCUS:
{current_focus}

HYPOTHESES:
{hypotheses}

DESIGN PRINCIPLES:
{design_principles}

LAST SPRINT: #{last_sprint['sprint_number'] if last_sprint else 'none'} \
({last_sprint['status'] if last_sprint else 'n/a'})
LAST PROCESS REVIEW: {last_review_line}

OPEN SPRINT BACKLOG ({len(backlog)} items):
{backlog_lines}

OPEN CANDIDATE APPROACHES ({len(candidates)} items):
{candidate_lines}
"""


def send(message: str) -> str:
    history = _load_history()
    live_state = _live_state_block()

    system = SYSTEM_PROMPT + "\n\n" + live_state

    messages = history + [{"role": "user", "content": message}]

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        system=system,
        messages=messages,
    )
    reply = response.content[0].text
    db.log_usage("team_leader", response.usage.input_tokens, response.usage.output_tokens)

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})
    _save_history(history)

    db.set_memory("team_leader", "status", "online")
    db.set_memory("team_leader", "last_greeting", reply)

    return reply


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m agents.team_leader.chat \"<message>\"", file=sys.stderr)
        print("       python -m agents.team_leader.chat -   (reads message from stdin)", file=sys.stderr)
        sys.exit(1)
    if sys.argv[1] == "-":
        user_message = sys.stdin.read()
    else:
        user_message = " ".join(sys.argv[1:])
    print(f"[{NAME}] {send(user_message)}")
