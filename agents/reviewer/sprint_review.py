"""Entry point for Ingrid's first Sprint Review -- a process retrospective
covering Sprints 1-5, distinct from her usual per-sprint content review.
Cadence: every 3 sprints going forward (confirmed with founder 2026-07-27),
following the agenda Sophie proposed at planning: factual recap, process
findings, root-cause analysis (why didn't the TEAM catch this?), fixes
already applied, structural prevention, backlog hygiene, DSR-phase check,
and a quantitative pulse-check.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

GROUND_TRUTH_INCIDENTS = """
THREE REAL PROCESS INCIDENTS FROM SPRINTS 1-5, ALL CAUGHT BY THE FOUNDER, NONE BY THE TEAM ITSELF:

INCIDENT 1 -- Scope-checklist gap (Sprint 2/3): the landscape scan and
Genially deep-dive silently covered only third-party commercial tools,
never checking foundation-model-native capabilities (Anthropic/OpenAI/
Google/Microsoft's own skills). Nobody on the team caught it during either
sprint's review. The founder caught it while scoping Sprint 4, by noticing
that findings about Anthropic/OpenAI were being described as "discoveries"
that should have already been covered. Fix applied: tools/scope_checklist.py
(4 required categories + a keyword pre-check), wired into Ingrid's own
persona (check scope-completeness, not just rigor) and Sophie's persona
(name covered/excluded categories before proposing a sprint).

INCIDENT 2 -- Shallow literature retrieval depth (Sprint 1 and Sprint 5):
every literature search call used max_results=5-6 per query. This was never
a screen-then-filter process -- it was a narrow top-N retrieval where
everything retrieved got written up, presented as if it were a
"comprehensive" or "full market analysis." The founder caught it by asking
directly why "16 papers analyzed" sounded thin for a comprehensive review.
Fix applied: agents/researcher/deep_literature_followup.py, 5 query framings
x 30 results x 2 sources = 259 unique papers, with Kenji's own honest
admission that ~76% of even that wider pool was noise.

INCIDENT 3 -- Conflating observation with solution-prescription (Sprint
2-5 synthesis language): phrasing like "nobody reasons about visual-form
selection" risked being read as "more reasoning is the missing piece" --
a solution diagnosis -- when the sprints had only established an
observation (no system demonstrates a content-audience-form connection).
The founder caught it by pointing out the actual research question is
open between at least two structurally different solution directions
(reasoning-based semantic linking, vs. an entirely new visualization
language beyond static 2D slides), and the team's language had started
presupposing the first one. Fix applied: rewrote the Sprint 5 cumulative
website text to state the observation plainly and name both directions as
open; reviewed the North Star for the same risk (founder confirmed no
change needed there).

A FOURTH, SMALLER STRUCTURAL GAP (not a content incident, but relevant to
backlog hygiene): no running backlog existed for (a) promising leads found
mid-brief (papers, patterns, tools) or (b) candidate sprint topics/questions
-- both got raised piecemeal in conversation and would have been easy to
lose track of. Fixed 2026-07-27: candidate_approaches and sprint_backlog
Postgres tables, both now checked by Sophie before sprint planning.
"""

QUANTITATIVE_DATA_TEMPLATE = """
QUANTITATIVE PULSE-CHECK (real data from Postgres):
{sprints_summary}

Reviews logged: {review_count} total, {approved_count} approved on first pass, {revision_count} required revision.

candidate_approaches: {candidate_count} entries, {candidate_open_count} still open.
sprint_backlog: {backlog_count} entries, {backlog_open_count} still open.
"""


def build_quantitative_data() -> str:
    sprints = db.list_sprints()
    sprints_summary = "\n".join(
        f"- Sprint {s['sprint_number']} [{s['status']}]: \"{s['question'][:100]}...\""
        for s in sprints
    )

    with db.get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM reviews")
        review_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM reviews WHERE result = 'approved'")
        approved_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM reviews WHERE result = 'needs_revision'")
        revision_count = cur.fetchone()[0]

    candidates = db.list_candidate_approaches(status=None)
    candidates_open = [c for c in candidates if c["status"] == "open"]
    backlog = db.list_backlog_items(status=None)
    backlog_open = [b for b in backlog if b["status"] == "open"]

    return QUANTITATIVE_DATA_TEMPLATE.format(
        sprints_summary=sprints_summary,
        review_count=review_count,
        approved_count=approved_count,
        revision_count=revision_count,
        candidate_count=len(candidates),
        candidate_open_count=len(candidates_open),
        backlog_count=len(backlog),
        backlog_open_count=len(backlog_open),
    )


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Sprint Review #1: process retrospective covering Sprints 1-5",
        description="First Sprint Review, cadence confirmed every 3 sprints going forward.",
    )

    quant_data = build_quantitative_data()

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "This is the first Sprint Review -- a process retrospective "
                    "covering Sprints 1-5, distinct from your usual per-sprint "
                    "content reviews. Follow Sophie's agenda exactly:\n\n"
                    "A) Factual recap (no judgment yet): what did the team "
                    "actually do across Sprints 1-5?\n"
                    "B) Process findings: what procedural weaknesses surfaced?\n"
                    "C) Root-cause analysis (THE key question): for each "
                    "finding, why didn't the TEAM catch it itself, rather than "
                    "the founder?\n"
                    "D) Fixes already applied: what changed as a result?\n"
                    "E) Structural prevention (most important for the founder): "
                    "what changes to our own process/tooling would make the "
                    "NEXT similar gap visible to the team, not the founder? Be "
                    "concrete and specific to each root cause from (C), not "
                    "generic advice.\n"
                    "F) Backlog hygiene: are candidate_approaches and "
                    "sprint_backlog actually being used?\n"
                    "G) DSR-phase check: are we still in the right phase?\n"
                    "H) Quantitative pulse-check: comment on the real numbers "
                    "below -- do they show anything a text-only review would "
                    "miss?\n\n"
                    f"{GROUND_TRUTH_INCIDENTS}\n\n"
                    f"{quant_data}\n\n"
                    "Be honest and specific. This review itself is subject to "
                    "the same standard you'd apply to a researcher's brief -- "
                    "don't let 'we fixed the instance' substitute for 'we "
                    "understand why it will recur if we don't change something "
                    "structural.' End with a clear, itemized list of concrete "
                    "structural actions -- each one naming what tool, persona, "
                    "or checklist it changes, not just a general intention."
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    review = response.content[0].text
    db.log_usage("ingrid", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"sprint-review-1-task-{task_id}",
        text=review,
        metadata={"agent": "ingrid", "type": "sprint_review"},
    )
    db.set_memory("ingrid", "sprint_review_1", review)
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="process_review", artifact_payload={"memory_key": "ingrid/sprint_review_1"},
    )

    process_review_id = db.create_process_review(
        covers_sprint_from=1,
        covers_sprint_to=5,
        conducted_by="ingrid",
        findings=review,
        actions_taken="See findings for itemized structural actions; to be applied as a follow-up.",
    )

    print(f"[{NAME}] Sprint Review #1 complete (process_review_id={process_review_id}).\n\n{review}")


if __name__ == "__main__":
    run()
