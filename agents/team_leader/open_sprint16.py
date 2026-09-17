"""Formally opens Sprint 16 -- "FGE Beyond Draco: Browser-Native
Generative Vocabulary + Composition".

Concept-only sprint (founder's explicit scope, 2026-09-17): no prototype,
no code, no UI, no new FVBS/Registrar/Blind-Scorer experiment. Reconceives
FGE (Sprint 15's top-ranked concept): the compositional principle
(primitives + composition rules) survives, but the primitive vocabulary
must NOT be inherited from Draco/Grammar-of-Graphics (a statistical-chart
vocabulary that structurally contradicts Design Principle #4 and the
North Star's "browser substrate has effectively unlimited expressive
ceiling" position) -- it must be derived from what is actually
composable in a browser and via generative models (images, motion,
interaction, diegetic embedding, multimodal views).

Five questions to answer before any prototyping (Sprint 17):
1. How can it concretely work? What is the value-add?
2. Are we reasonably confident this doesn't already exist (checked
   against our own prior research and candidate approaches)?
3. How can it scale?
4. How would a working tool be derived from it (transition plan only,
   not the prototype itself)?
5. What are the technical prerequisites?

Includes a new temporary specialist role, per the founder's approval:
Knowledge Systems Architect (2 days, design/architecture only, no code,
no data access beyond anonymized examples) -- addresses question 3
(scaling) specifically.
"""
from agents.permissions import require_tool
from agents.team_leader.persona import NAME
from tools import db

QUESTION = (
    "Reconceiving FGE (Sprint 15's top-ranked concept, Form Grammar "
    "Extension): the compositional principle (primitives + composition "
    "rules) is kept, but the primitive vocabulary must be derived from "
    "what is actually composable in a browser and via generative models "
    "-- not inherited from Draco/Grammar-of-Graphics's 7-mark "
    "statistical-chart vocabulary, which structurally contradicts Design "
    "Principle #4 and the North Star's browser-substrate position. "
    "Before any prototyping: (1) How can this concretely work, and what "
    "is the value-add? (2) Are we reasonably confident this concept "
    "doesn't already exist, checked against our own prior research? "
    "(3) How can it scale? (4) How would a working tool be derived from "
    "it (transition plan, not the prototype)? (5) What are the technical "
    "prerequisites? Deliverable: a concept-ready spec package. No "
    "prototype, no code, no UI, no new experiment -- concepts only. The "
    "prototype is Sprint 17."
)

PHASE0_BRIEF = """SPRINT 16 -- PHASE 0 KICKOFF BRIEF (Sophie, for the whole team)

CORE REFRAME (founder, 2026-09-17, after direct critique of Sprint 15's
FGE concept): Draco was measurement infrastructure for Sprint 13/14's
experiments -- a cheap, deterministic, reproducible reference for
automated scoring at scale. It was never a product-architecture claim.
Its 7-mark vocabulary comes from the Grammar-of-Graphics tradition
(Wilkinson, Vega-Lite) -- a language for statistical charts, not for
communication in general. If FGE just extends Draco's vocabulary with
more chart types, it stays inside exactly the box Design Principle #4
and the North Star want to break out of.

WHAT SURVIVES: the compositional principle itself -- describing a visual
form as constituent primitives + a composition rule (why is a raincloud
a raincloud: density-estimate + strip-jitter + box-summary, combined to
show three things at once) is a sound, general representational
strategy. It is not inherently chart-bound.

WHAT CHANGES: the primitive vocabulary must be derived from what is
actually composable in a browser and via generative models -- layout,
motion, interaction, illustration, data-binding, annotation, narrative
control, generated imagery, diegetic embedding (Candidate #10) -- not
from Draco's inherited mark-type list. "Going beyond Draco's 7 marks" is
now understood as the cheapest first slice of a much larger vocabulary,
not the destination.

NON-GOALS FOR SPRINT 16 (explicit):
- No prototype, no code, no UI.
- No new FVBS/Registrar/Blind-Scorer experiment.
- No broad new literature/market landscape scan -- only a "closest
  neighbors" check against what this team has already found (Candidates
  #1, #2, #4, #10, #11 and ingested full texts).
- No large corpus collection -- at most 3-5 illustrative examples as
  thinking aids.
- No framework/build decision -- Sprint 17's transition plan is
  hypothetical scoping, not a commitment.

DELIVERABLE PACKAGE (end of sprint):
1. Concept Spec (answers Q1, Q3, Q4, Q5)
2. Prior-art / "does this already exist?" memo (answers Q2)
3. Prototype Transition Plan for Sprint 17 (no code)
4. Open Questions / Risks (feeds the backlog)

REVIEW GATES: a mid-sprint Ingrid check (is this still browser-native, or
sliding back into "charts + Grammar of Graphics"?) and a final Ingrid
gate (value-add is a testable claim, prior-art check is plausible,
Sprint 17 plan is small and testable, not another testbed)."""

TEMP_ROLE_BRIEF = """TEMPORARY ROLE, Sprint 16 only: Knowledge Systems Architect.

Scope: design/architecture only. No code. No data access beyond
anonymized/illustrative examples. Engaged for question 3 (scaling)
specifically: sketch scaling strategies for a knowledge base of this
kind across three levels -- (a) knowledge coverage (more domains/
audiences/goals), (b) expressive vocabulary (more primitive categories:
motion, interaction, illustration, generated imagery), (c) operating
model (how quality is maintained: versioning, QA, drift detection, weak
supervision, retrieval-vs-structure tradeoffs). Mandate ends when
question 3's deliverable is handed to Priya/Sophie for the Concept Spec
-- same "temporary, single-sprint, narrowly scoped" discipline as the
Registrar and Blind Scorer roles."""


def run() -> None:
    require_tool("team_leader", "write_backlog")
    db.set_memory("team_leader", "status", "online")

    sprint_id = db.get_sprint_id(16)
    if sprint_id is None:
        sprint_id = db.create_sprint(16, QUESTION)
        print(f"[{NAME}] Sprint 16 created (sprint_id={sprint_id}).")
    else:
        print(f"[{NAME}] Sprint 16 already exists (sprint_id={sprint_id}), not recreated.")

    db.set_memory("team_leader", "sprint16_phase0_brief", PHASE0_BRIEF)
    db.set_memory("team_leader", "sprint16_temp_role_brief", TEMP_ROLE_BRIEF)
    db.set_memory("team_leader", "current_focus",
                  "Sprint 16 open: FGE reconceived beyond Draco (browser-native/generative "
                  "vocabulary). Concepts-only, no prototype. Knowledge Systems Architect "
                  "(temp role) engaged for scaling question. Prototype is Sprint 17.")

    print(f"[{NAME}] Question: {QUESTION}")
    print(f"[{NAME}] Phase 0 brief stored as team_leader/sprint16_phase0_brief "
          f"({len(PHASE0_BRIEF)} chars).")
    print(f"[{NAME}] Temp role brief stored as team_leader/sprint16_temp_role_brief "
          f"({len(TEMP_ROLE_BRIEF)} chars).")


if __name__ == "__main__":
    run()
