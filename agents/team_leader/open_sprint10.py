"""Applies Ingrid's two pre-opening actions and opens Sprint 10.

Ingrid's confirmation review (ingrid/sprint10_design_confirmation) returned
"CONFIRMED -- sprint may open", subject to two fast actions:
  A. A flagging mechanism for Pass 4, which otherwise has no verification step
     (every other pass has an external check; the synthesis step, historically
     where this project overclaims, had none).
  C. One sentence in Mateo's buildability instruction, so a field-6-only
     review cannot silently confirm a test that only fits a simpler proxy of
     the concept.

She stated neither requires a v3 proposal, so these are recorded as a dated
amendment appended to the existing proposal -- the same pattern used for
Sprint 6's Gemini amendment, where the original text was preserved and the
change documented rather than silently rewritten.

There is no existing "open a sprint" entrypoint: log_sprint.py only closes.
This creates the sprint row so Sprint 10 does not repeat Sprint 8, which sat
as in_progress with completed_at NULL because nothing ever opened or closed
it formally.
"""
from agents.permissions import require_tool
from tools import db

SPRINT_NUMBER = 10
SPRINT_QUESTION = (
    "Design & Development, design half: what rival concepts exist for the "
    "communication layer, and how would each actually work? Four isolated "
    "passes -- Priya blind (no prior-art seeds), Priya sighted (seeds shown), "
    "Kenji per-concept prior-art verification, Sophie synthesis into a "
    "comparative decision input. Generates alternatives before building or "
    "validating any of them."
)

AMENDMENT = """

-------------------------------------------------------------------------------
AMENDMENT (2026-08-19) -- Ingrid's two pre-opening actions, applied
-------------------------------------------------------------------------------

Recorded per ingrid/sprint10_design_confirmation ("CONFIRMED -- sprint may
open", subject to these two). Neither required a v3 proposal.

ACTION A -- Pass 4 verification flagging (Ingrid's New Problem A).
Pass 4 was the only pass without an external check. Passes 1-3 each have one:
Ingrid gates Pass 1's input log, Kenji verifies concepts against prior art,
Mateo checks field 6 buildability. Pass 4's "no new claims" constraint was
stated but unverified, and Pass 4 is precisely where this project's synthesis
has historically overclaimed.

  Mechanism, agreed: in the plain-language comparison section of Pass 4,
  Sophie must mark every sentence that has no direct referent in a template
  field from Passes 1-3. Marked sentences are Sophie's own observations, not
  sprint findings, and must be visually separated in the output the founder
  receives. A Pass 4 with no marked sentences and no direct referents is
  itself a flag. Ingrid reviews the marks, not the whole synthesis -- this
  keeps the check cheap enough not to become a bottleneck.

ACTION C -- Mateo's separability caveat (Ingrid's New Problem C).
Bounding Mateo to field 6 only prevents scope expansion but assumes a
falsification test can be judged without reading the mechanism in fields 1-2.
It sometimes cannot: a test may be buildable for a simpler proxy than the
concept actually proposes.

  Added to Mateo's instruction, verbatim: "If you cannot evaluate whether this
  test is buildable without understanding the mechanism described in fields 1
  and 2, say so explicitly in your one-sentence reasoning rather than
  guessing. 'Cannot judge without the mechanism' is a valid verdict and is
  more useful than a confident wrong one."

NOT APPLIED, recorded as open (Ingrid accepted the deferral, founder decision):
recommended items 8 (browser-medium vs. ideal-form gap), 9 (Kenji pass
self-identification), 10 (positive success criterion). Residual risks per her
confirmation: medium anchoring during concept generation; no data on how far
the Pass 3 blinding held; no positive success criterion in the template. All
three to be revisited before Sprint 11 if a concept is selected for building.

Ingrid's New Problem B (goal-space category overlap) was assessed by her as
low severity and deliberately not escalated -- the template will surface it if
it matters in practice.
"""


def run() -> None:
    require_tool("team_leader", "log_sprint")
    db.set_memory("team_leader", "status", "online")

    proposal = db.get_memory("team_leader", "sprint10_proposal")
    if not proposal:
        raise SystemExit("No sprint10_proposal found.")

    if "AMENDMENT (2026-08-19)" in proposal:
        print("[Sophie Marchetti] Amendment already present — not appending twice.")
    else:
        db.set_memory("team_leader", "sprint10_proposal", proposal + AMENDMENT)
        print("[Sophie Marchetti] Ingrid's actions A and C appended as a dated amendment.")

    sprint_id = db.get_sprint_id(SPRINT_NUMBER)
    if sprint_id is None:
        sprint_id = db.create_sprint(SPRINT_NUMBER, SPRINT_QUESTION)
        print(f"[Sophie Marchetti] Sprint 10 opened (sprint_id {sprint_id}).")
    else:
        print(f"[Sophie Marchetti] Sprint 10 already exists (sprint_id {sprint_id}).")

    db.create_task(
        created_by="team_leader",
        assigned_to="priya",
        title="Sprint 10 Pass 1: generate concepts blind (no prior-art seeds)",
        description=(
            "Concepts against the seven-field template, derived from the constraint "
            "set and Sprints 6-8 failure data only. Full input to be logged at "
            "concept_designer/sprint10_pass1_input for Ingrid's gate before Pass 2."
        ),
    )

    print(f"[Sophie Marchetti] Pass 1 task opened for Priya. "
          f"Pass 2 blocked until Ingrid confirms the Pass 1 input log.")


if __name__ == "__main__":
    run()
