"""Entry point for Ingrid's second Sprint Review -- process retrospective
covering Sprints 6-9. Same agenda as Sprint Review #1 (sprint_review.py):
factual recap, process findings, root-cause analysis, fixes already
applied, structural prevention, backlog hygiene, DSR-phase check,
quantitative pulse-check. Overdue: was due after Sprint 8 per the
every-3-sprints cadence, not conducted until Sprint 9's close -- the review
itself is late, which is one of the incidents fed into it below.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

GROUND_TRUTH_INCIDENTS = """
REAL INCIDENTS FROM SPRINTS 6-9, WITH WHO ACTUALLY CAUGHT EACH ONE (this is
the key variable to track -- Process Review #1 found the team's self-catch
rate was zero across Sprints 1-5; this window has a mix):

INCIDENT 1 -- Gemini gap closed in two real steps, not one (Sprint 6):
Sprint 6's behavioral test excluded Gemini (no API key) and shipped with
that gap explicitly flagged. The founder later provided a key and asked to
close the gap "as if we'd done it in Sprint 6" -- Claude (orchestrating)
pushed back on literally rewriting the timeline (the live site already
published the exclusion) and proposed bundling the follow-up under Sprint 6
with an honest dated amendment instead. Founder accepted. CAUGHT BY: Claude
(orchestrating session), a self-imposed integrity check, not founder- or
Ingrid-initiated.

INCIDENT 2 -- Sprint 7 adversarial-pairs construction gap + Naledi's own
methodological self-catch: Ingrid's review found one pair's (AP2) canonical-
form claim was underspecified (a model's normal-condition choice, a box
plot, was also defensible against the claimed canonical bar-chart baseline).
CAUGHT BY: Ingrid, in review, as designed. Separately and more notably:
Naledi identified her own major limitation unprompted -- the
"culturally-scripted-scenario problem," that some adversarial scenarios
(finance audit, VP status check) are recognizable professional scripts
models could pattern-match on rather than genuinely reasoning from context.
CAUGHT BY: Naledi herself, in her own brief, before Ingrid's review even
started.

INCIDENT 3 -- Sprint 8: three real pipeline bugs, caught three different
ways: (a) a token-truncation JSON failure -- CAUGHT BY: Claude, reading the
actual output length rather than trusting a success message. (b) A missing
content_summary data-flow link that caused Stage 2 to generate completely
off-topic chart content (homelessness-service data in a heat-mitigation
document) -- CAUGHT BY: Claude, reading the rendered HTML output line by
line rather than trusting the automated structural-validation check, which
does not and cannot catch this class of error. (c) A chart-width overflow
bug whose FIRST fix (container-based responsive sizing) silently broke
rendering entirely in a real browser -- CAUGHT BY: the founder, only
because he actually opened the file. Every automated check available said
this fix was fine; it wasn't. No amount of code-level review would have
caught it without a real browser.

INCIDENT 4 -- Sprint 8 never got added to the website: the standing rule
(update the site after every sprint close) was followed for every sprint
except Sprint 8 -- silently skipped, sat unnoticed through Sprint 8's
entire close and into Sprint 9. CAUGHT BY: Claude, incidentally, while
updating the site for Sprint 9's close -- not by any review, not by the
founder, not by any checklist. Nothing in the process would have caught
this on its own; it was luck that Sprint 9's close required touching the
same section of the site.

INCIDENT 5 -- Process Review #2 (this review) is itself the incident it's
reviewing: due after Sprint 8 per the team's own every-3-sprints cadence,
not conducted until Sprint 9's close. Same discovery circumstance as
Incident 4 -- found incidentally while fixing Incident 4, not by any
scheduled check. Sophie's persona has no mechanism that actually surfaces
"a Process Review is now due" -- the cadence exists as a stated rule with
no enforcement.
"""

QUANTITATIVE_DATA_TEMPLATE = """
QUANTITATIVE PULSE-CHECK (real data from Postgres, Sprints 6-9):
{sprints_summary}

Reviews logged in this window: {review_count} total, {approved_count} approved (incl. after revision), {revision_count} required at least one revision pass.
Sprints requiring 2+ review passes before approval: {multi_pass_sprints}

candidate_approaches: {candidate_count} entries total, {candidate_open_count} still open.
sprint_backlog: {backlog_count} entries total, {backlog_open_count} still open.
New backlog items opened during Sprints 6-9: {new_backlog_items}
"""


def build_quantitative_data() -> str:
    sprints = [s for s in db.list_sprints() if 6 <= s["sprint_number"] <= 9]
    sprints_summary = "\n".join(
        f"- Sprint {s['sprint_number']} [{s['status']}]: \"{s['question'][:100]}...\""
        for s in sprints
    )

    sprint_ids = [db.get_sprint_id(n) for n in range(6, 10)]
    sprint_ids = [sid for sid in sprint_ids if sid is not None]

    with db.get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT sprint_id, result FROM reviews WHERE sprint_id = ANY(%s) ORDER BY sprint_id, created_at",
            (sprint_ids,),
        )
        rows = cur.fetchall()

    review_count = len(rows)
    approved_count = sum(1 for _, r in rows if r == "approved")
    revision_count = sum(1 for _, r in rows if r == "needs_revision")
    per_sprint = {}
    for sid, _ in rows:
        per_sprint[sid] = per_sprint.get(sid, 0) + 1
    multi_pass_sprints = sum(1 for count in per_sprint.values() if count > 1)

    candidates = db.list_candidate_approaches(status=None)
    candidates_open = [c for c in candidates if c["status"] == "open"]
    backlog = db.list_backlog_items(status=None)
    backlog_open = [b for b in backlog if b["status"] == "open"]
    new_backlog_items = [b for b in backlog if b["created_at"].year == 2026 and b["created_at"].month == 8]

    return QUANTITATIVE_DATA_TEMPLATE.format(
        sprints_summary=sprints_summary,
        review_count=review_count,
        approved_count=approved_count,
        revision_count=revision_count,
        multi_pass_sprints=multi_pass_sprints,
        candidate_count=len(candidates),
        candidate_open_count=len(candidates_open),
        backlog_count=len(backlog),
        backlog_open_count=len(backlog_open),
        new_backlog_items=len(new_backlog_items),
    )


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Sprint Review #2: process retrospective covering Sprints 6-9",
        description="Overdue -- was due after Sprint 8, conducted at Sprint 9's close.",
    )

    quant_data = build_quantitative_data()
    prior_review = db.get_memory("ingrid", "sprint_review_1") or ""

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Sprint Review #2 -- covering Sprints 6-9. This review is "
                    "itself late (due after Sprint 8, run now at Sprint 9's "
                    "close) -- that lateness is Incident 5 below and should "
                    "be treated with the same rigor as any other finding, "
                    "not glossed over because it's about this very process.\n\n"
                    "Follow the same agenda as Sprint Review #1:\n\n"
                    "A) Factual recap: what did the team actually do across "
                    "Sprints 6-9?\n"
                    "B) Process findings: what procedural weaknesses "
                    "surfaced?\n"
                    "C) Root-cause analysis: for each finding, why did or "
                    "didn't the team catch it itself?\n"
                    "D) Fixes already applied.\n"
                    "E) Structural prevention: concrete, specific changes "
                    "to tooling/persona/process -- not generic advice.\n"
                    "F) Backlog hygiene.\n"
                    "G) DSR-phase check.\n"
                    "H) Quantitative pulse-check.\n\n"
                    "ONE THING TO DO DIFFERENTLY FROM REVIEW #1: that review "
                    "found the team's self-catch rate was zero across "
                    "Sprints 1-5 -- every substantive issue was founder-"
                    "caught. This window is different: several incidents "
                    "below were caught by Claude or Naledi, not the founder. "
                    "Assess this honestly -- is this a real improvement, or "
                    "does it look better only because 'Claude caught it' is "
                    "doing a lot of work across very different kinds of "
                    "catches (a self-imposed integrity check vs. reading "
                    "output carefully vs. pure luck of touching the right "
                    "file for an unrelated reason)? Distinguish real "
                    "process improvement from incidental luck.\n\n"
                    "ALSO ADDRESS DIRECTLY: Incident 5 is the review process "
                    "itself failing to self-trigger on schedule. What "
                    "structural fix would make 'a Process Review is now "
                    "due' visible without relying on incidental discovery "
                    "the way this one was found?\n\n"
                    f"{GROUND_TRUTH_INCIDENTS}\n\n"
                    f"{quant_data}\n\n"
                    f"FOR REFERENCE, PROCESS REVIEW #1'S FULL FINDINGS "
                    f"(Sprints 1-5, so you can assess whether the S1-S10 "
                    f"structural actions from that review actually held up "
                    f"across Sprints 6-9, or quietly lapsed):\n\n{prior_review}\n\n"
                    "Be honest and specific. End with a clear, itemized list "
                    "of concrete structural actions, each naming what tool, "
                    "persona, or checklist it changes."
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    review = response.content[0].text
    db.log_usage("ingrid", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"sprint-review-2-task-{task_id}",
        text=review,
        metadata={"agent": "ingrid", "type": "sprint_review"},
    )
    db.set_memory("ingrid", "sprint_review_2", review)
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="process_review", artifact_payload={"memory_key": "ingrid/sprint_review_2"},
    )

    process_review_id = db.create_process_review(
        covers_sprint_from=6,
        covers_sprint_to=9,
        conducted_by="ingrid",
        findings=review,
        actions_taken="See findings for itemized structural actions; to be applied as a follow-up.",
    )

    print(f"[{NAME}] Sprint Review #2 complete (process_review_id={process_review_id}).\n\n{review}")


if __name__ == "__main__":
    run()
