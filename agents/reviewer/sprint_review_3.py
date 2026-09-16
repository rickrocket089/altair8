"""Entry point for Ingrid's third Sprint Review -- process retrospective
covering Sprints 10-12. Same agenda as Reviews #1 and #2: factual recap,
process findings, root-cause analysis, fixes already applied, structural
prevention, backlog hygiene, DSR-phase check, quantitative pulse-check.
Due after Sprint 12's close (3 sprints since Review #2, which covered 6-9)
-- caught on time this round, at Sophie's own PROCESS REVIEW STATUS check
before scoping Sprint 13, not discovered late as Review #2 was.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

GROUND_TRUTH_INCIDENTS = """
REAL INCIDENTS FROM SPRINTS 10-12, WITH WHO ACTUALLY CAUGHT EACH ONE:

INCIDENT 1 -- Sprint 10, Kenji's own inadequacy self-catch: his first
verification pass declared itself inadequate for 4 of 6 concepts and he
requeried before presenting anything. CAUGHT BY: Kenji himself, before
Ingrid's review.

INCIDENT 2 -- Sprint 10, a concept's novelty claim killed by a literature
retrieval the team had not done before choosing to pursue it: round-2
querying surfaced Mackinlay's APT (1986), which had already solved what
Concept 3 claimed nobody had. CAUGHT BY: Kenji, in a required re-verification
round -- but only AFTER the concept had already been presented as a
candidate, meaning the novelty gap existed in the team's own output for one
full round before being caught internally, not by the founder.

INCIDENT 3 -- Sprint 10, Ingrid's own honesty about non-merit selection: she
stated plainly in her close review that C1 won partly because it was
best-evidenced against the team's OWN retrieval capability limits (one of
the only two concepts with a runnable falsification test), not necessarily
because it was the strongest concept on the merits. CAUGHT BY: Ingrid,
unprompted, about her own review's blind spot.

INCIDENT 4 -- Sprint 11, two real bugs found by building, not reviewing: a
"structurally unavoidable" claim-check defined so strictly it matched almost
nothing (would have shipped silently dead), and a collapsed test case that
never fired because two scenarios had been merged onto one claim. CAUGHT BY:
the build/test process itself, not a review step -- these were invisible to
spec review and only surfaced once code ran against real data.

INCIDENT 5 -- Sprint 11, a 26-day stall with no process trigger: the Standing
Obligations Check (built after Review #2 specifically to catch exactly this
class of gap) only runs when a NEW sprint is being planned -- the one
condition that cannot occur while a sprint is already stuck open. Nothing
fired for 26 days. CAUGHT BY: nobody, structurally -- the sprint simply
resumed when the founder returned. Two backlog items were opened to make a
stalled sprint raise itself; as of Sprint 12's close, unclear whether either
has actually been implemented as running code (verify this in the review).

INCIDENT 6 -- Sprint 11, browser verification moved before review instead of
after: three prior sprints had shipped prototypes unverified in a real
browser (the code literally printed an apology for it). This sprint changed
that, and headless Chrome found 6 defects in about 20 minutes, including two
that broke the default state a reader sees first. CAUGHT BY: the
orchestrating session, choosing to verify before shipping rather than after
-- a process change applied, not just an incident found.

INCIDENT 7 -- Sprint 11, Ingrid reported a finding against her own process
and then struck it: she initially flagged Kenji's prior-art brief as
"truncated mid-sentence," which was false -- the review script itself had
sliced the brief at 16,000 characters before she ever saw it. She caught
this at a confirmation pass, struck the finding, and named her own failure
explicitly ("I treated a truncated display as ground truth"). CAUGHT BY:
Ingrid, self-correcting her own prior output -- a genuine self-catch, not
founder-prompted.

INCIDENT 8 -- Sprint 11, infrastructure gotchas on restart: the dashboard
container crashed (ModuleNotFoundError: agents.permissions) because its
compose service never mounted the agents/ directory, and every Anthropic API
call inside the container failed with CERTIFICATE_VERIFY_FAILED because a
host security product (Kaspersky) intercepts TLS and its root CA was never
installed into the container's trust store. CAUGHT BY: the orchestrating
session, debugging real error output rather than assuming the environment
was fine.

INCIDENT 9 -- Sprint 12 (and the pivot session immediately before it),
multiple real bugs and gaps caught by direct verification rather than
trusting a script's own success signal:
  (a) an acquisition-list script's own formatting function read a dict key
      (`pdf_url`) that OpenAlex results never populate -- the real field is
      `fulltext_url` -- silently degrading every "FREE FULL TEXT" link in an
      entire acquisition brief to a non-PDF landing page. CAUGHT BY: the
      orchestrating session, when an attempted auto-download kept failing
      and the actual URLs were inspected directly.
  (b) a founder-downloaded PDF titled to match a canonical textbook
      (Munzner's "Visualization Analysis and Design") turned out, on
      inspection of extraction length and PDF metadata, to be a 5-slide
      excerpt from an unrelated talk on the author's own site, not the book.
      CAUGHT BY: the orchestrating session, because an extraction of only 5
      pages from a 6.7MB file was suspicious enough to check rather than
      accept at face value.
  (c) a second founder-downloaded PDF, intended to be Reiter & Dale's 1997
      journal article, was actually a different, solo-authored, earlier 1996
      Reiter arXiv preprint with an overlapping but non-identical title.
      CAUGHT BY: the orchestrating session, reading the extracted text's
      own header rather than trusting the filename.

INCIDENT 10 -- Sprint 12, Ingrid's review caught a subtler failure mode than
usual -- not overclaiming, but two other things: (a) two papers' findings
were written up as "equally consistent with both accounts" (a symmetric,
inconclusive framing) when the evidence actually leaned weakly asymmetric
against one account -- a real precision loss, though it did not change the
overall null-result verdict; (b) more significantly, Kenji's draft brief
proposed HOW Sophie should reinterpret her own sprint-closing criterion to
fit a null result, rather than surfacing the ambiguity and putting the
decision to her explicitly. CAUGHT BY: Ingrid, in review -- and this is the
second time in three sprints (see Review #2's own finding on scope) that a
researcher's brief has quietly made a decision that belonged to Sophie or
the founder.

INCIDENT 11 -- Sprint 12, a live-chat recall gap, twice in one session:
Sophie's new interactive chat interface (built this same session -- the
project's first) told the founder twice that already-resolved work was
still open or unconfirmed (an already-completed literature check; and
already-ingested full-text papers), because her live-state context included
Postgres `agent_memory` but not the on-disk record of which PDFs had
actually been processed. CAUGHT BY: the founder, both times, mid-
conversation -- not by Sophie or any review step. Fixed structurally (the
chat script's context now lists ingested papers), not just corrected in the
moment.

INCIDENT 12 -- Sprint 12 close, a website stat drifted stale for the third
time in this project's history: "papers screened" had previously been
corrected 10->16 (2026-07-27) and later to 270; by this session it had
silently drifted to 1,252 while the real count was already 1,381 -- caught
again within the SAME session, immediately after a manual correction, by one
more research task quietly adding ~130 more papers. CAUGHT BY: the founder,
noticing the pattern a third time and asking for it to be fixed structurally
rather than corrected again by hand -- led to a real sync script being built
this time, not just another one-off edit.
"""


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")

    hypotheses = db.get_memory("team_leader", "hypotheses") or "(missing)"
    design_principles = db.get_memory("team_leader", "design_principles") or "(missing)"
    north_star = db.get_memory("team_leader", "north_star") or "(missing)"

    sprints = db.list_sprints()
    outcomes = "\n\n".join(
        f"--- Sprint {s['sprint_number']} ---\nQUESTION: {s['question']}\n\nOUTCOME: {s['outcome']}"
        for s in sorted(sprints, key=lambda s: s["sprint_number"])
        if s["status"] == "completed" and s["sprint_number"] in (10, 11, 12)
    )
    backlog = db.list_backlog_items(status="open")
    backlog_lines = "\n".join(f"#{b['id']} [{b['priority']}] {b['title']}" for b in backlog)
    candidates = db.list_candidate_approaches(status="open")
    candidate_lines = "\n".join(f"#{c['id']} [{c['priority']}] {c['title']}" for c in candidates)

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Process Review #3: Sprints 10-12",
        description="Every-3-sprints cadence, caught on time at Sophie's PROCESS REVIEW STATUS check.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Conduct Process Review #3, covering Sprints 10-12. Same agenda "
            "as Reviews #1 and #2: factual recap, process findings, "
            "root-cause analysis one level past 'we fixed the instance', "
            "fixes already applied, structural prevention (name the specific "
            "tool/persona/checklist that changes), backlog hygiene, DSR-phase "
            "check, and the quantitative self-catch-rate pulse-check Review "
            "#1 started and Review #2 found 'partial, not uniform.'\n\n"
            "SPECIFIC THINGS THIS REVIEW MUST DO:\n\n"
            "1. UPDATE THE SELF-CATCH-RATE TRACKING. Review #1: zero across "
            "Sprints 1-5. Review #2: partial credit for Sprints 6-9 (genuine: "
            "Naledi's and Claude's self-catches; no credit: founder-caught "
            "browser bug, missed website update, the review's own lateness). "
            "Categorize each of the 12 incidents above by who actually caught "
            "it -- team self-catch, orchestrating-session catch (is that "
            "'the team' or not? make an explicit judgment call and justify "
            "it), or founder catch. Give the honest rate for this window and "
            "say whether it's trending up, down, or flat against the first "
            "two windows.\n\n"
            "2. INCIDENT 5 (the 26-day stall) IS A PROCESS REVIEW #2 FIX "
            "THAT DIDN'T WORK. Review #2 built the Standing Obligations Check "
            "specifically to catch stalled sprints, and it structurally "
            "cannot fire while a sprint IS stalled -- only at the next "
            "planning session. Two backlog items were opened to address this "
            "at Sprint 11's close. Check `sprint_backlog` yourself for "
            "whether either exists and whether it describes an actual "
            "running mechanism or just a restated intention. This is exactly "
            "the kind of 'rules exist, enforcement doesn't' pattern your own "
            "Review #2 named as the dominant failure mode -- say plainly "
            "whether it has recurred.\n\n"
            "3. INCIDENT 10 IS A REPEAT OF A PATTERN, NOT A NEW ONE. A "
            "researcher's draft making a decision that belonged to Sophie or "
            "the founder. Has this happened before in the record you have "
            "(check the sprint outcomes below)? If it's a repeat, that's a "
            "persona-level gap (Kenji's or the general researcher "
            "instructions), not a one-off precision slip -- say what "
            "specific instruction should be added and where.\n\n"
            "4. INCIDENT 9 AND INCIDENT 12 ARE THE SAME SHAPE: something "
            "silently degrades (a bug, a stale number) and only gets caught "
            "because someone checked real output instead of trusting a "
            "success signal or a prior manual fix. This has now happened "
            "enough times (the truncated-brief incident in Sprint 11, the "
            "pdf_url bug, the stat drift, the Munzner mislabeling) that it "
            "may deserve a named standing principle, not four separate "
            "fixes. Do you agree, and if so what should that principle say "
            "and where should it live?\n\n"
            "5. THE NEW CHAT INTERFACE (Incident 11) is genuinely new "
            "infrastructure, built THIS session -- Sophie's first real "
            "conversational interface with the founder rather than one-shot "
            "task scripts. It was already partially fixed in-session (the "
            "ingested-papers list was added to her live-state context after "
            "the second recall gap). Assess whether that fix is sufficient "
            "or whether other categories of mechanical state (open Docker "
            "tasks, recent commits, dashboard state) could cause the same "
            "class of gap next time, and if so what the general principle "
            "should be for what belongs in a persona's live-state block "
            "versus what's acceptable to leave out.\n\n"
            "6. CUMULATIVE SYNTHESIS CHECK (standing, every review): does "
            "the website's public synthesis language, across Sprints 10-12, "
            "still accurately separate observation from prescription? Sprint "
            "12 in particular reports a clean NULL result on hypothesis 6 -- "
            "check that the site's language doesn't quietly imply the null "
            "result means less than it does, or that Backlog #23 is already "
            "underway when it is only recommended.\n\n"
            "7. DSR-PHASE CHECK. Sprint 12 was deliberately placed back in "
            "'Problem Identification' after four sprints in 'Design & "
            "Development' -- a non-linear move the team made consciously and "
            "explained publicly. Is that the right call, structurally? Does "
            "anything about the team's DSR bookkeeping need to change to "
            "accommodate a real backward move, or was a one-off explanation "
            "sufficient?\n\n"
            "End with itemized structural actions (same format as Reviews #1 "
            "and #2 -- S11, S12, etc., continuing the numbering), each naming "
            "the specific tool, persona instruction, or checklist it changes. "
            "Log this review via your own judgment of what "
            "`create_process_review()` should store.\n\n"
            f"{GROUND_TRUTH_INCIDENTS}\n\n"
            f"=== SPRINT 10-12 OUTCOMES (full text) ===\n{outcomes}\n\n"
            f"=== CURRENT OPEN BACKLOG ===\n{backlog_lines}\n\n"
            f"=== CURRENT OPEN CANDIDATE APPROACHES ===\n{candidate_lines}\n\n"
            f"=== HYPOTHESES ===\n{hypotheses}\n\n"
            f"=== DESIGN PRINCIPLES ===\n{design_principles}\n\n"
            f"=== NORTH STAR ===\n{north_star}\n"
        )}],
    ) as stream:
        response = stream.get_final_message()

    review = response.content[0].text
    db.log_usage("ingrid", response.usage.input_tokens, response.usage.output_tokens)

    review_id = db.create_process_review(
        covers_sprint_from=10,
        covers_sprint_to=12,
        conducted_by="ingrid",
        findings=review,
        actions_taken="See findings text for itemized S11+ structural actions.",
    )

    db.set_memory("ingrid", "process_review_3", review)
    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"process-review-3-task-{task_id}",
        text=review,
        metadata={"agent": "ingrid", "type": "process_review_3"},
    )
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/process_review_3", "review_id": review_id},
    )

    print(f"[{NAME}]\n\n{review}")
    print(f"\n\n--- {len(review)} chars, stored as ingrid/process_review_3 (process_review id={review_id}) ---")


if __name__ == "__main__":
    run()
