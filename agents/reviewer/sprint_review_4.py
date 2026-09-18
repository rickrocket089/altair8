"""Entry point for Ingrid's fourth Sprint Review -- process retrospective
covering Sprints 13-15. Same agenda as Reviews #1-#3: factual recap,
process findings, root-cause analysis, fixes already applied, structural
prevention, backlog hygiene, DSR-phase check, self-catch-rate pulse-check.

Due after Sprint 15's close (3 sprints since Review #3, which covered
10-12) -- caught late this round: Sprint 15 was never formally marked
completed until Sprint 16's own close gate caught the gap, which is
itself one of this review's incidents.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

GROUND_TRUTH_INCIDENTS = """
REAL INCIDENTS FROM SPRINTS 13-15, WITH WHO ACTUALLY CAUGHT EACH ONE:

INCIDENT 1 -- Sprint 13, a manual-truncation-continuation fabricated fake
statistics: feeding Ingrid's gate review only the last ~1200 chars of a
truncated prior response (instead of full context) caused her to
hallucinate specific numbers (N=600, 4 models, 3 conditions) that did not
exist. CAUGHT BY: the orchestrating session, before the fabricated review
was stored -- led directly to building tools/llm_call.py (stream_complete,
real continuation on full context) as standing infrastructure.

INCIDENT 2 -- Sprint 13 pilot, max_tokens=600 silently truncated 2/27 real
experimental outputs (not documents -- the measurement itself). CAUGHT BY:
the orchestrating session, checking stop_reason/finish_reason explicitly
after Incident 1 made truncation a named risk; fixed by raising the ceiling
and adding real truncation checks to all three model-calling functions.

INCIDENT 3 -- Sprint 13 close, Kenji's synthesis overclaimed ("tilts toward
Reading B") on evidence Ingrid found didn't actually support that lean --
probe data cited as support was equally consistent with the rejected
reading. CAUGHT BY: Ingrid, in gate review.

INCIDENT 4 -- Sprint 14, Draco's own cost-ranked candidate selection was
ASSUMED to satisfy the project's F1/F2/F3 criterion (structural validity)
without being checked -- Ingrid's spot-check on her own random 4-scenario
sample found 7/16 candidates (44%) failed F1/F2/F3 despite being
Draco-satisfiable. This was a real, load-bearing methodological finding,
not a minor gap -- it meant the entire candidate-generation pipeline
needed a real, systematic filter built (backlog38_candidate_filter.py),
which then found 11/20 scenarios short of the target candidate count and
4/20 down to a single candidate. CAUGHT BY: Ingrid, spot-checking rather
than trusting "Draco completed without an exception" as evidence of
correctness -- exactly the standing principle this project already holds.

INCIDENT 5 -- Sprint 14, Kenji asserted (did not verify) that Draco's
constraints were unchanged since Sprint 13. CAUGHT BY: Ingrid, flagging the
unverified claim; then actually verified for real (git log +
importlib.metadata on the running container) by the orchestrating session,
which also tightened the draco pin from >=2.0.0 to ==2.0.1 as a result --
a real future-drift risk closed, not just a claim corrected.

INCIDENT 6 -- Sprint 14, a real script bug in gate_sprint14_registrar_lock.py:
the LOCK/NOT-LOCKED auto-detection matched a section header
("## CHECK 6 -- GATE VERDICT") instead of the actual verdict line
("GATE VERDICT: LOCK"), so a real LOCK was printed and nearly treated as
NOT LOCKED. CAUGHT BY: the orchestrating session, reading Ingrid's actual
review text instead of trusting the script's own printed summary --
fixed with a precise regex, and the same imprecise-detection class of bug
recurred and was caught again in Sprint 16's close-gate scripts, built
correctly from the start there specifically because of this incident.

INCIDENT 7 -- Sprint 14, Ingrid's gate review referenced "two document-
currency questions Kenji flagged in his retrieval log output-verification
note" -- a document that was never part of the materials actually supplied
to her for that task. CAUGHT BY: the orchestrating session, recognizing the
reference didn't match any real input and flagging it as a likely
hallucination rather than treating it as a real blocking precondition.

INCIDENT 8 -- Sprint 14, score_fvbs.py's first production run crashed on
scenario 8 of 20 (empty LLM response) with NO incremental persistence --
7 scenarios' worth of real, already-paid-for API calls were at risk of
being silently discarded. CAUGHT BY: the orchestrating session, via the
crash itself; fixed with per-scenario persistence and retry-on-empty
before rerunning.

INCIDENT 9 -- Sprint 14, a real combination-logic bug: the FVBS scorer
asked the SAME LLM call to both determine f1/f2/f3 sub-judgments AND
synthesize a final_outcome label, and 21/120 trials had a final_outcome
that directly contradicted their own stated sub-judgments (every
NOT-IN-SET-but-structurally-valid case got mislabeled STRUCTURAL_FAIL) --
precisely the "one failure type masking another" pattern the protocol
itself warned against, produced BY the scorer rather than avoided by it.
CAUGHT BY: the orchestrating session, systematically cross-checking stated
final_outcome against stated sub-fields across all 120 records rather than
trusting the model's own aggregation; fixed by recomputing the combination
deterministically in Python going forward, not asking the LLM to do it.

INCIDENT 10 -- Sprint 14, a second, independent scorer error found while
verifying Ingrid's own gate-review Condition 2: 3 of scenario S14's
NOT-IN-SET trials explicitly nominated "line chart" nominations despite
S14 having `line` as a real valid candidate -- directly contradicting a
matching rule the same scoring pass applied correctly elsewhere in the
same run. CAUGHT BY: the orchestrating session, pulling and reading the
actual nominated-form text behind aggregate NOT-IN-SET counts rather than
trusting the counts themselves.

INCIDENT 11 -- Sprint 14 close, Kenji's REVISED synthesis (after being
corrected for Sprint 13's overclaim) swung to the opposite failure: it
UNDER-claimed a genuine, in-band confirmatory result as merely
"directionally informative but not conclusive." CAUGHT BY: Ingrid, naming
this explicitly as the mirror-image error of the earlier overclaim --
the same persona correcting too far in the opposite direction after a
prior correction, not a new independent mistake.

INCIDENT 12 -- Sprint 15/16 boundary, a real process gap: Sprint 15 was
opened, fully executed (4 concepts produced, reality-checked, reviewed,
acted on by the founder), and never formally marked completed in
Postgres. This silently broke Process Review cadence tracking (the
standing status-check tool reported "2 sprints since last review" when
Sprint 15's un-closed status was itself the reason the number looked
lower than reality). CAUGHT BY: Ingrid, during Sprint 16's own close gate,
cross-checking real cadence facts rather than accepting the status block
at face value -- but her own FIRST attempt to reason about this produced
an incorrect "4 sprints, overdue" conclusion by speculating that the
supplied real data must be stale, rather than trusting the real,
freshly-queried facts she was given. CAUGHT BY (the correction to
Ingrid's own reasoning): the orchestrating session, verifying Sprint
15/16's actual `status` field directly rather than accepting either her
speculation or the original stale framing.

INCIDENT 13 -- Sprint 16, a real, propagated counting error: multiple
scripts (written by the orchestrating session) told Mateo there were
"6 seed contracts" when the actual specified set was 8 (5 statistical +
3 non-chart). Mateo's substantive work was unaffected (he named all 8
individually throughout), but the mislabeled total propagated across two
full task scripts before being caught. CAUGHT BY: Sophie, during her own
synthesis pass, cross-checking the stated count against the enumerated
list rather than repeating the number she was given.

INCIDENT 14 -- Sprint 16, Sophie's OWN revision (meant to fix Ingrid's
first close-gate findings) introduced a genuine internal contradiction:
it pre-resolved a technical design question (the CheckResult schema
reflecting Mateo's slot/composition-rule bifurcation finding) while ALSO
listing the review of that same finding as a mandatory pre-build gate --
these cannot both be true as written. CAUGHT BY: Ingrid, on the SECOND
close-gate pass, reading the revision closely enough to catch that fixing
one round's findings had created a new, different inconsistency rather
than assuming a revision pass is automatically clean.

INCIDENT 15 -- Sprint 15/16, the single most consequential correction in
this window came from the FOUNDER, not the team: after Sprint 15 selected
FGE (Form Grammar Extension) as the concept to pursue, the founder
directly challenged why the design inherited Draco's chart-vocabulary as
its primitive set at all, correctly identifying that this contradicted
Design Principle #4 and the North Star's browser-substrate position. This
reframing (compositional principle kept, vocabulary re-derived from
browser/generative capability instead of Draco) became the actual
substance of Sprint 16. Separately, the founder also caught that neither
Barbara Minto's nor Gene Zelazny's work -- both directly relevant to the
business-communication knowledge-layer question -- had ever been
referenced or ingested by the research team across the entire project,
despite Zelazny's chart-choice framework being close prior art for
exactly what Sprint 15/16 were trying to build from scratch. NEITHER of
these was caught by Kenji's own literature process at any point before
the founder raised them directly.
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
        if s["status"] == "completed" and s["sprint_number"] in (13, 14, 15)
    )
    backlog = db.list_backlog_items(status="open")
    backlog_lines = "\n".join(f"#{b['id']} [{b['priority']}] {b['title']}" for b in backlog)
    candidates = db.list_candidate_approaches(status="open")
    candidate_lines = "\n".join(f"#{c['id']} [{c['priority']}] {c['title']}" for c in candidates)

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Process Review #4: Sprints 13-15",
        description="Every-3-sprints cadence, caught late (Sprint 15's own close was also late).",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Conduct Process Review #4, covering Sprints 13-15. Same "
            "agenda as Reviews #1-#3: factual recap, process findings, "
            "root-cause analysis one level past 'we fixed the instance', "
            "fixes already applied, structural prevention (name the "
            "specific tool/persona/checklist that changes), backlog "
            "hygiene, DSR-phase check, and the self-catch-rate pulse-"
            "check (Review #3's window: 'trending up, down, or flat').\n\n"
            "SPECIFIC THINGS THIS REVIEW MUST DO:\n\n"
            "1. UPDATE THE SELF-CATCH-RATE TRACKING. Categorize each of "
            "the 15 incidents above by who actually caught it -- team "
            "self-catch (a persona catching its own or another persona's "
            "error), orchestrating-session catch, or founder catch. Give "
            "the honest rate for this window and say whether it's "
            "trending up, down, or flat against Review #3's window. Be "
            "specific about Incident 15 -- the founder catching both the "
            "Draco-vocabulary contradiction AND the Minto/Zelazny gap is "
            "a genuinely bad self-catch-rate signal for exactly the kind "
            "of thing Kenji's research role exists to catch. Say so "
            "plainly, don't soften it.\n\n"
            "2. A NEW RECURRING PATTERN: IMPRECISE VERDICT-DETECTION "
            "SCRIPTS (Incident 6). This is the second review in a row "
            "where a review-verdict-parsing bug caused a real gate "
            "result to be misreported. Is a single named standing "
            "principle warranted here (e.g. 'verdict detection must use "
            "an anchored regex on the literal verdict line, never a "
            "fuzzy substring match') -- and if so, does it actually get "
            "applied consistently afterward, or does each new gate script "
            "reinvent this? Check the actual pattern across Incident 6 "
            "and the two Sprint 16 close-gate scripts referenced in the "
            "sprint outcomes below.\n\n"
            "3. THE SELF-GRADING / COMBINED-JUDGMENT PATTERN (Incident 9). "
            "Asking one LLM call to both produce sub-judgments AND "
            "synthesize them into a final combined verdict produced a "
            "real, systematic error (21/120 trials). Is this a specific "
            "instance of a more general principle this project should "
            "hold -- 'any combination/aggregation logic over already-"
            "produced structured judgments should be computed "
            "deterministically in code, not re-asked of the model'? "
            "State it precisely if so, and name where else in the "
            "current pipeline (Sprint 16's CheckResult scoring, for "
            "instance) this principle needs to be actively applied "
            "going forward, not just observed in hindsight.\n\n"
            "4. INCIDENT 12 IS A REVIEW-#2-STYLE 'RULES WITHOUT "
            "ENFORCEMENT' RECURRENCE. Sprint completion tracking has no "
            "mechanism forcing a sprint to actually be marked complete "
            "when its work concludes -- it relies on someone remembering "
            "to run the close script. This is the same class of gap as "
            "Review #2's original finding and Review #3's Incident 5 "
            "(the stalled-sprint check). Does this warrant a structural "
            "fix (e.g. a periodic or session-open check that flags any "
            "sprint with status='in_progress' whose work has clearly "
            "concluded, similar to Sophie's existing stalled-sprint "
            "alert), or is founder/session vigilance sufficient given how "
            "quickly it was actually caught this time?\n\n"
            "5. INCIDENT 15's DEEPER QUESTION. Kenji's literature-"
            "grounding process (candidate approaches, ingested full "
            "texts, deep_literature_followup runs) has now run across "
            "13+ sprints without surfacing either Minto or Zelazny, "
            "despite both being foundational, widely-known frameworks "
            "directly on-point for a business-communication visualization "
            "project. Is this a retrieval-scope gap (the academic-"
            "database-only search tools structurally cannot reach "
            "practitioner/business literature), a directive gap (nobody "
            "ever asked Kenji to look outside academic sources), or "
            "something else? Name the specific, structural fix -- not just "
            "'search more broadly next time.'\n\n"
            "6. CUMULATIVE SYNTHESIS CHECK (standing, every review): does "
            "the website's public synthesis language, across Sprints "
            "13-15, still accurately separate observation from "
            "prescription? Sprint 14 in particular reports a real, "
            "non-degenerate confirmatory result (53.9% FVBS) -- check "
            "the site doesn't either overclaim it as definitive or "
            "undersell it as merely suggestive, given Sprint 14's own "
            "synthesis had to be corrected once in each direction before "
            "landing on accurate language.\n\n"
            "7. DSR-PHASE CHECK. Sprints 13-14 were confirmatory "
            "evaluation work (Design Science Research 'Evaluation' "
            "phase); Sprint 15-16 moved back to 'Define Objectives of a "
            "Solution' after the founder's critique. Is the team's DSR "
            "bookkeeping keeping pace with these real phase transitions, "
            "or has it drifted from what's actually being done?\n\n"
            "End with itemized structural actions (same format as "
            "Reviews #1-#3 -- continuing the S-numbering), each naming "
            "the specific tool, persona instruction, or checklist it "
            "changes. Log this review via your own judgment of what "
            "`create_process_review()` should store.\n\n"
            f"{GROUND_TRUTH_INCIDENTS}\n\n"
            f"=== SPRINT 13-15 OUTCOMES (full text) ===\n{outcomes}\n\n"
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
        covers_sprint_from=13,
        covers_sprint_to=15,
        conducted_by="ingrid",
        findings=review,
        actions_taken="See findings text for itemized S-numbered structural actions.",
    )

    db.set_memory("ingrid", "process_review_4", review)
    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"process-review-4-task-{task_id}",
        text=review,
        metadata={"agent": "ingrid", "type": "process_review_4"},
    )
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/process_review_4", "review_id": review_id},
    )

    print(f"[{NAME}]\n\n{review}")
    print(f"\n\n--- {len(review)} chars, stored as ingrid/process_review_4 (process_review id={review_id}) ---")


if __name__ == "__main__":
    run()
