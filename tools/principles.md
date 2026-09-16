# Standing Principles

Named findings from Process Reviews that apply broadly enough to warrant a
single canonical statement, cross-referenced from wherever they're enforced,
rather than being re-derived per persona or rediscovered per incident.

## The Reported-Success Trap

**Named:** Process Review #3 (2026-09-16), covering Sprints 10-12.

**Statement:** A mechanism reporting success is evidence that it ran without
error, not that its output matches the intended semantics. Whenever a
script, agent, or process produces output that will be consumed downstream
without further review — a link, a file, a number, a brief — verify at
least one sample of the actual output against the intended result before
treating the run as complete. "It ran" is not "it worked."

**Why this got named rather than left as separate bugs:** five real
instances hit this project across three sprints, in different subsystems,
with the same causal shape — a signal existed (a script finished, a file
downloaded, a stat updated) and was trusted without checking what it
actually produced:
1. A review script silently sliced a brief at 16,000 characters; Ingrid
   treated the truncated display as ground truth and filed a false finding
   before catching and striking it herself (Sprint 11).
2. An acquisition-list script's formatter read a dict key (`pdf_url`) that
   OpenAlex results never populate — the real field is `fulltext_url` —
   degrading every "free full text" link in an entire brief to a non-PDF
   landing page (Sprint 12).
3. A founder-downloaded PDF titled to match a canonical textbook turned out,
   on inspection, to be a 5-slide excerpt from an unrelated talk (Sprint 12).
4. A second founder-downloaded PDF, meant to be one paper, was a different,
   earlier, solo-authored preprint with an overlapping title (Sprint 12).
5. A website stat ("papers screened") drifted stale three separate times
   across the project's history, twice within the same session (Sprint 12
   close).

**Where this is enforced:**
- `agents/researcher/persona.py` — Kenji verifies output before treating it
  as usable.
- `agents/reviewer/persona.py` — Ingrid treats links/files/stats in any
  brief as unverified unless the sprint log shows a direct inspection.
- `agents/team_leader/persona.py` — Sophie's sprint-close checklist asks
  explicitly whether each script's actual output (not just its exit
  status) was inspected.
- `tools/sync_website_stats.py` — the concrete fix for instance 5: a real
  script that patches the stat from live DB state, not a one-off hand-edit
  repeated every time someone happens to notice drift.

## Rules Without Enforcement Recur at the Meta-Level

**Named:** Process Review #3 (2026-09-16).

**Statement:** When a Process Review finds "a rule exists but nothing
enforces it," the fix must be running code, not a backlog item that
restates the rule with more emphasis. A backlog item describing a desired
behavior ("a stalled sprint must raise itself") is not a fix for the
absence of enforcement — it is one more rule without enforcement, at one
level up. This is exactly what happened to Process Review #2's Standing
Obligations Check: built specifically to catch stalled sprints, it only
runs at sprint planning — the one moment that structurally cannot occur
while a sprint is already stuck — and the backlog items opened afterward
(#30, #31) sat with no implementation for an entire sprint.

**The test to apply:** before closing any backlog item meant to fix an
enforcement gap, ask whether the fix is a persona instruction alone, or a
persona instruction backed by code that runs automatically at the relevant
trigger point (session start, sprint close, publish). Instruction-only
fixes for enforcement gaps should be treated as provisional, not closed.

## Continuation Grounding

**Named:** Sprint 13, Phase 0 gate review (2026-09-16), the same day the
Reported-Success Trap itself was named.

**Statement:** When a model reply is truncated at a token limit and gets
continued in a fresh call, the continuation must be grounded in the full
source material (the original document/protocol being discussed, and
everything the reply itself already committed to), not just the tail end of
the truncated text. A continuation fed only the last ~1000-1500 characters
of context has nothing to check new claims against, and will fill gaps with
plausible-sounding but fabricated specifics.

**What happened:** Ingrid's Sprint 13 Phase 0 gate review was truncated
mid-sentence inside its contamination-prevention procedure. The continuation
call was given only the last 1200 characters of her own text as context.
When it reached the final "Gate Verdict" section, it fabricated a sample
size, model count, and condition count that appear nowhere in the actual
study (the real design is 20 scenarios, 3 models, 2 conditions — the
continuation invented "N=600 scenarios x 4 models x 3 conditions" and an
unrelated power-calculation framework). Caught by comparing the continuation
against the real protocol before it was shown to anyone or stored as final;
the fabricated section was discarded and regenerated with the full protocol
and the reviewer's own prior checks as grounding.

**The rule:** any truncation-continuation call must include (a) the full
original source document being analyzed, not a summary or an excerpt, and
(b) enough of the already-generated reply that the continuation stays
consistent with commitments already made — but (a) matters more than (b),
because a continuation with only its own tail and no source material has no
way to catch itself inventing plausible-sounding facts. Verify a
continuation's substantive claims against the source before trusting it,
the same way any other Reported-Success Trap instance gets checked.
