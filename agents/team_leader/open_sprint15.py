"""Formally opens Sprint 15 -- "Knowledge Layer Concepts (#11-first)".

Concepts-only sprint per the founder's explicit scoping decision
(2026-09-16): no prototype, no code, no new experiments. Priya develops
3-5 distinct concepts for a visualization-knowledge layer (centered on
Candidate Approach #11, optionally informed by #1 TVIR and #2 Structured
Visualization Design Knowledge), blind to each other and to any "best
direction" steer, per the same discipline as Sprint 10's blind concept
pass. The prototype is deliberately deferred to Sprint 16.
"""
from agents.permissions import require_tool
from agents.team_leader.persona import NAME
from tools import db

QUESTION = (
    "How can a visualization-knowledge layer (representation, feeding "
    "mechanism, runtime query) be designed so that it (a) is model-"
    "agnostic, (b) makes audience/goal first-class, and (c) addresses "
    "the form-selection unreliability observed in Sprint 14 (FVBS "
    "~53.9%, NOT-IN-SET ~26.7%), without collapsing back into legacy "
    "deck constraints? Deliverable: 3-5 clearly distinct concepts, "
    "centered on Candidate Approach #11 (corpus of existing business-"
    "communication artifacts as a knowledge structure), optionally "
    "combined with #1 (TVIR) and #2 (Structured Visualization Design "
    "Knowledge). No prototype, no code, no new experiments -- concepts "
    "only. The prototype is Sprint 16."
)

INPUT_BRIEF = """INPUT BRIEF for Priya -- blind concept development, Sprint 15.

CONTEXT (6 sentences):
1. Sprint 13/14 showed: even among structurally valid options, models do
   not choose the audience-optimal form on ~54% of trials (FVBS 53.9%).
2. The mechanism (internalized structure vs. convention-reproduction)
   remains open.
3. NOT-IN-SET is high (~27%), partly caused by a real Draco-vocabulary
   ceiling (the tool/schema cannot express certain form families models
   reach for).
4. The goal is not more measurement apparatus -- it's a knowledge layer
   that practically stabilizes or makes form selection negotiable.
5. Focus is Candidate Approach #11 (corpus of business-communication
   artifacts as a knowledge structure for form selection), optionally
   combined with #1 (TVIR) and #2 (Structured Visualization Design
   Knowledge).
6. No prototype this sprint -- concepts only. The prototype is Sprint 16.

HARD CONSTRAINTS (non-negotiable):
C1 -- Model-agnostic (Design Principle #2): must not depend on a
      specific model's capabilities.
C2 -- Not deck-bound (Design Principle #4): must not force output back
      into PowerPoint-style boxes; HTML/frontend experience stays open.
C3 -- Audience/goal first-class (Hypothesis #2): the knowledge layer must
      explicitly represent audience/goal or be directly compatible with
      doing so.
C4 -- Control via NL iteration (Hypothesis #3): must not require users to
      manually edit visual primitives.
C5 -- Operationally queryable: usable at runtime (retrieve/score/
      constrain/plan), not just a library to read.
C6 -- Updatable: must be clear how the knowledge grows (seed ->
      continuous feeding).

DO NOT:
- No new experiments, no rubric/scoring machinery.
- No full literature search -- only the permitted inputs below.
- No implementation proposal that is at its core "rebuild Draco" without
  a clear distinct benefit.

PERMITTED INPUTS (Kenji provides only these):
- A one-page summary of Sprint 14 learnings (FVBS/NOT-IN-SET causes, no
  raw data).
- Links/abstracts for Candidate #1 (TVIR), #2 (Structured Visualization
  Design Knowledge), and #11.
- The controlled audience/goal vocabulary (6x6) as a possible schema
  element.

OUTPUT TEMPLATE (strict, max 1 page per concept, 3-5 concepts):
1. Name + one-sentence thesis
2. Representation: what is the data structure? (cases, rules, programs,
   ontology+embeddings, ...)
3. Feeding: sources + extraction mechanism (manual/LLM-assisted/parsing)
4. Update: how does it grow? (versioning, QA, drift)
5. Runtime use: how does it act on generation? (retrieve exemplars /
   constrain search / plan steps / evaluate candidates)
6. How it addresses the Sprint 14 ceiling: which failure modes (FVBS,
   NOT-IN-SET) does it directly mitigate?
7. Falsifier: what would quickly devalue this concept? (concretely
   testable)
8. Risks: 3 bullets (including "does it reinforce convention?")
"""


def run() -> None:
    require_tool("team_leader", "write_backlog")
    db.set_memory("team_leader", "status", "online")

    sprint_id = db.get_sprint_id(15)
    if sprint_id is None:
        sprint_id = db.create_sprint(15, QUESTION)
        print(f"[{NAME}] Sprint 15 created (sprint_id={sprint_id}).")
    else:
        print(f"[{NAME}] Sprint 15 already exists (sprint_id={sprint_id}), not recreated.")

    db.set_memory("team_leader", "sprint15_input_brief_for_priya", INPUT_BRIEF)
    db.set_memory("team_leader", "current_focus",
                  "Sprint 15 open: Knowledge Layer Concepts (#11-first), concepts-only, "
                  "no prototype. Priya to develop 3-5 blind concepts per the input brief.")

    print(f"[{NAME}] Question: {QUESTION}")
    print(f"[{NAME}] Input brief stored as team_leader/sprint15_input_brief_for_priya "
          f"({len(INPUT_BRIEF)} chars).")


if __name__ == "__main__":
    run()
