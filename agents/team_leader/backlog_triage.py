"""Sophie's first backlog triage pass, per her own new persona instruction
(Process Review #3, 2026-09-16, S30): before opening a new sprint, every
open backlog item gets an explicit disposition -- active (addressed in the
next few sprints), conditional (name the condition that revives it), or
parked (name why) -- rather than sitting as undifferentiated "open."

Run once, ahead of scoping Sprint 13 for Backlog #23. Founder's explicit
instruction, same session: #23 is the single highest-priority item right
now, ahead of the other three items already marked 'high'.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.team_leader.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"


def run() -> None:
    require_tool("team_leader", "write_backlog")
    db.set_memory("team_leader", "status", "online")

    backlog = db.list_backlog_items(status="open")
    candidates = db.list_candidate_approaches(status="open")
    hypotheses = db.get_memory("team_leader", "hypotheses") or ""
    current_focus = db.get_memory("team_leader", "current_focus") or ""

    # Real sprint/review state -- omitting this caused the first run of this
    # script to have Sophie fabricate her own PROCESS REVIEW STATUS block
    # ("Sprints 1-10" covered by Review #3, which never happened) rather
    # than admit she didn't have the numbers. Same class of gap this whole
    # session has been fixing elsewhere; fixed here too before rerunning.
    sprints = db.list_sprints()
    reviews = db.list_process_reviews()
    last_sprint = sprints[-1] if sprints else None
    last_review = reviews[-1] if reviews else None
    review_status_facts = (
        f"Last sprint completed: #{last_sprint['sprint_number']} "
        f"(status={last_sprint['status']})\n"
        f"Last Process Review: covers sprints "
        f"{last_review['covers_sprint_from']}-{last_review['covers_sprint_to']}, "
        f"conducted_by={last_review['conducted_by']}\n"
        f"Sprints since last review: "
        f"{last_sprint['sprint_number'] - last_review['covers_sprint_to']}"
        if last_sprint and last_review else "No sprint/review data found."
    )

    backlog_block = "\n\n".join(
        f"#{b['id']} [{b['priority']}] {b['title']}\n{b['description'][:600]}"
        for b in backlog
    )
    candidate_block = "\n".join(
        f"#{c['id']} [{c['priority']}] {c['title']}" for c in candidates
    )

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="team_leader",
        title="Backlog triage pass before Sprint 13",
        description="Process Review #3's S30 requirement, run once before Sprint 13 scoping.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model=MODEL, max_tokens=8000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Run the backlog triage Process Review #3 required of you before "
            "any new sprint gets scoped. Your PROCESS REVIEW STATUS and "
            "SESSION-OPEN STALL CHECK blocks must be grounded in the real "
            "sprint/review facts given below -- do not estimate or "
            "reconstruct these numbers from context; if you're unsure, say "
            "so rather than stating a specific number you're not certain of. "
            "26 open items below. For EACH one, "
            "give: DISPOSITION (active / conditional / parked), and one "
            "tight sentence of reasoning -- not a paragraph, this is "
            "triage, not re-litigation.\n\n"
            "DEFINITIONS:\n"
            "- ACTIVE: will genuinely be addressed in the next 2-3 sprints. "
            "Say roughly when/how if you can.\n"
            "- CONDITIONAL: not now, but name the SPECIFIC condition that "
            "would revive it -- not 'later' but an actual trigger.\n"
            "- PARKED: not now, and no specific trigger -- say why plainly "
            "rather than pretending it's still live.\n\n"
            "CONTEXT THAT SHOULD DRIVE SEVERAL OF THESE CALLS:\n"
            "- Backlog #23 is the founder's explicit top priority as of "
            "today, ahead of the other three 'high' items (#14, #15, #24) -- "
            "Sprint 13 is being scoped for it now, all 4 phases in one "
            "sprint. Anything #23 makes irrelevant, redundant, or "
            "premature should be marked accordingly, not left as an "
            "independent 'active' item competing for the same attention.\n"
            "- Sprint 12 closed with a clean null result on hypothesis 6 "
            "from the literature. Anything premised on the literature "
            "eventually answering H6 should be reconsidered.\n"
            "- Several C1-renderer items (#26, #27, #28, #29) may now be "
            "better read as inputs INTO #23's Phase 0/1 design (the C1 "
            "artifact is what any behavioral study would show participants) "
            "rather than separate polish work -- consider whether some "
            "should be marked conditional on #23's design needing them, not "
            "parked or independently active.\n\n"
            "After the per-item table, give ONE PARAGRAPH: what this triage "
            "reveals about the backlog as a whole -- is it healthy, "
            "over-stuffed with low-value items, missing anything given "
            "where the project actually is right now?\n\n"
            f"=== REAL SPRINT/REVIEW STATE (ground truth, use this exactly) ===\n"
            f"{review_status_facts}\n\n"
            f"=== 26 OPEN BACKLOG ITEMS ===\n{backlog_block}\n\n"
            f"=== OPEN CANDIDATE APPROACHES, FOR CONTEXT ===\n{candidate_block}\n\n"
            f"=== CURRENT FOCUS ===\n{current_focus}\n\n"
            f"=== HYPOTHESES ===\n{hypotheses}\n"
        )}],
    ) as stream:
        response = stream.get_final_message()

    triage = response.content[0].text
    db.log_usage("team_leader", response.usage.input_tokens, response.usage.output_tokens)

    db.set_memory("team_leader", "backlog_triage_1", triage)
    vectorstore.remember(
        collection_name="team_leader_memory",
        doc_id=f"triage-task-{task_id}",
        text=triage,
        metadata={"agent": "team_leader", "type": "backlog_triage"},
    )
    db.update_task(
        task_id, status="completed", result=triage,
        artifact_type="brief",
        artifact_payload={"memory_key": "team_leader/backlog_triage_1"},
    )

    print(f"[{NAME}]\n\n{triage}")
    print(f"\n\n--- {len(triage)} chars, stored as team_leader/backlog_triage_1 ---")


if __name__ == "__main__":
    run()
