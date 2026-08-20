"""Stores the deep-analysis sprint plan to the backlog, and opens Sprint 11.

The plan was designed in conversation with the founder (2026-08-20). He then
found a real gap in it: every hypothesis presupposed that models CAN reason
about visual form and differed only on what blocks the output. Each of those
hypotheses implies a remedy Altair8 could build. The two hypotheses whose truth
would say "do not build this" were the two missing.

That is a structural bias toward hypotheses that keep the project viable --
the same shape as the Sprint 4 blind spot, where a team built on Claude did not
naturally audit Claude as the failure. Here, a team built on a premise did not
naturally audit the premise. Founder-caught at design stage, before the sprint
ran. Recorded for Process Review #3, due at Sprint 12.

H0 and H6 are now in, each with a condition that makes it falsifiable rather
than merely stated.

Sequencing: founder placed this AFTER the C1 prototype.
"""
from agents.permissions import require_tool
from tools import db

SPRINT_NUMBER = 11
SPRINT_QUESTION = (
    "Build the C1 Commitment Audit prototype -- an agent that audits its own claims "
    "as evidence / inference / assumption / assertion with continuous confidence, and "
    "renders an argument map where visual weight derives from confidence rather than "
    "rhetorical emphasis. Two Ingrid conditions gate the build: a targeted "
    "argument-visualization prior-art search before any external framing, and a formal "
    "specification of the minimum-spanning-argument scaffold before Mateo starts."
)

TITLE = "Deep analysis: WHY do models fail on purpose-to-visualization mapping?"

DESCRIPTION = """Founder-initiated 2026-08-20, scheduled AFTER the C1 prototype.
Founder confirmed up front: publish the result either way, including if it
undercuts the project's premise.

THE METHOD SHIFT THAT MAKES THIS DIFFERENT
Sprints 6, 7 and the Gemini addition all used one method: ask the model to
reason, then inspect the reasoning. That cannot establish causation, and Naledi
said so herself in Sprint 6 -- she could not rule out that accurate, specific
reasoning was produced post-hoc rather than driving the form choice. No number
of additional scenarios fixes this. So: INTERVENTION, NOT OBSERVATION. Do not
ask the model why it chose; manipulate what it has and watch whether the choice
moves.

HYPOTHESES (H1-H5 designed with the founder; H0 and H6 added after he caught
that every original hypothesis presupposed model capability)

H0  No competence, unfixable. What looks like form reasoning is surface
    pattern-matching; scaffolding, reframing and reordering all fail.
    H1-H5 each imply a remedy. H0 implies there is none.
H1  Elicitation gap -- competence exists but is never surfaced unprompted.
    Predicts: supplying an explicit decision framework largely fixes output.
H2  Post-hoc rationalisation -- reasoning follows the form rather than driving
    it. Predicts: corrupting the audience premise leaves the form unchanged
    while the justification bends to fit.
H3  Frame anchoring -- "which chart?" is so dominant that "should this be a
    chart at all?" is never reached. Predicts: ablating audience/goal barely
    moves the form; non-chart forms occur at near-zero base rate.
H4  Modality gap -- the model cannot simulate what a reader perceives.
    Predicts: it fails to evaluate its OWN rendered output shown back as an
    image.
H5  Training-signal absence -- the reasoning that produces charts is almost
    never written down; models saw outputs, never decisions. Predicts:
    plausible-but-inconsistent rationales; consistency collapses across reruns
    of identical inputs.
H6  The models are not the problem -- there may be no correct answer to fail
    at. Mackinlay's APT solved formal derivation of visual form from data
    structure in 1986 (retrieved in Sprint 10) and business communication is
    still PowerPoint. A correct answer existed and did not change practice.

PHASE 0 -- Define the failure operationally before explaining it. We have never
defined what counts as a failure instance; that is why Sprint 10's criterion (b)
failed and why Phase C keeps slipping. Note also that Sprint 8's confabulated
chart turned out ARCHITECTURAL (a data-flow gap between stages), not a model
limitation, and Sprints 6-7 found models DO reason about audience. Do not walk
in assuming models fail. Establishing the failure is smaller than we have been
saying is a legitimate outcome.

PHASE 1 -- Establish the phenomenon at scale. 20 scenarios x 3 models x multiple
runs, deliberately NON-SCRIPTED per Naledi's culturally-scripted-scenario
finding (no finance audits, no VP status checks -- those are pattern-matchable
from training). Two rigor upgrades this team has never applied:
  - PRE-REGISTRATION: write and store each hypothesis's predicted outcome
    BEFORE running anything. Cheapest available defence against fitting the
    analysis to whatever came back.
  - BLIND SCORING: a model that did not generate the output scores it against a
    rubric, blind to condition. Naledi asked for blind scoring after Sprint 6
    and never got it. Ingrid validates the rubric before use; the absence of
    human raters is disclosed, not glossed.

PHASE 2 -- The causal interventions. Content held constant across all four:
  ABLATION       strip audience and goal entirely. Form unchanged => H3.
  CORRUPTION     supply a FALSE audience premise. If reasoning is causally
                 upstream the form should follow the false premise; if the form
                 holds while the justification adapts, that is H2 and it is the
                 cleanest post-hoc detector available in black box.
  ORDER          force form commitment BEFORE reasoning vs. reasoning first.
                 Identical quality => the reasoning step is decorative.
  SUPPLY         hand the model an explicit audience->goal->form framework.
                 Failure largely disappears => H1, an elicitation gap rather
                 than a capability gap. Most consequential single result for
                 what Altair8 builds: it would mean the layer's job is
                 scaffolding, not new reasoning.

  CEILING CONDITION (makes H0 falsifiable -- required, not optional): maximal
  support -- explicit framework AND audience AND goal AND the rendered output
  to inspect AND multiple attempts. Still failing under all of that is H0.
  Without this condition the sprint literally cannot return "models cannot do
  this."

PHASE 3 -- Modality probe. Render the model's own output and show it back as an
image: what would a reader take from this? Uses complete_with_image, already
built for Sprint 9's template-reproduction test. A model that cannot evaluate
its own artifact visually means H4 is live, and the architecture needs a
render-and-inspect loop rather than a better prompt. Absorbs open backlog item
#9 (tool-access vs. no-tool-access) and answers Ingrid's Sprint 4 question about
whether base models internalised this reasoning through training.

GROUND-TRUTH EXISTENCE CHECK (makes H6 testable without readers -- required):
before asking whether models pick the right form, ask whether a right form
EXISTS. Do the three models converge with each other on a given scenario? Does
one model converge with ITSELF across reruns? Do published authorities -- APT's
effectiveness criteria, the dataviz form heuristic, the visualization-
recommendation literature -- agree with each other on the same cases? If none
converge, "the model chose wrong" is unmeasurable and the failure lies in the
task's under-determination, not the reasoner. Ten sprints in, nobody has asked
whether a correct answer exists.

WHAT STAYS OUT OF REACH, STATED UP FRONT
No activations, no probes, no training-data inspection -- there is no
interpretability access and there will not be. We can establish THAT reasoning
is or is not causally upstream; never WHAT inside the model makes it so. We
also still cannot test whether any output communicates better, because that
needs readers. That exclusion is deliberate: this sprint is scoped to the
deepest question answerable WITHOUT the capability the team lacks, which is
exactly why it is runnable while Phase C is not.

COST: larger than one 2-day sprint. Phases 0-1 are one sprint; Phase 2 is the
expensive one and probably its own; Phase 3 is small and can ride along.

PREREQUISITE BEFORE DESIGN IS FINALISED: Kenji should check whether these
interventions have already been run on this question. The team was caught twice
in Sprint 10 claiming novelty that prior art had covered."""


def run() -> None:
    require_tool("team_leader", "write_backlog")
    db.set_memory("team_leader", "status", "online")

    existing = {i["title"] for i in db.list_backlog_items()}
    if TITLE in existing:
        print("= backlog item already exists — not duplicating.")
    else:
        item_id = db.create_backlog_item(
            title=TITLE, description=DESCRIPTION,
            proposed_by="founder", priority="high",
        )
        print(f"+ backlog [high] id={item_id}: {TITLE}")
        print(f"  ({len(DESCRIPTION)} chars of plan stored)")

    sprint_id = db.get_sprint_id(SPRINT_NUMBER)
    if sprint_id is None:
        sprint_id = db.create_sprint(SPRINT_NUMBER, SPRINT_QUESTION)
        print(f"\n[Sophie Marchetti] Sprint 11 opened (sprint_id {sprint_id}).")
    else:
        print(f"\n[Sophie Marchetti] Sprint 11 already open (sprint_id {sprint_id}).")

    print("\nPROCESS REVIEW STATUS")
    print("  Last Sprint Review covered: Sprints 6-9 (process_reviews id=3)")
    print("  Sprints since last review:  1 (Sprint 10)")
    print("  Sprint Review due this sprint? No — due at Sprint 12.")

    print("\nSprint 11 gates, both from Ingrid's Sprint 10 close conditions:")
    print("  1. Targeted argument-visualization prior-art search — before C1 is framed externally.")
    print("  2. Minimum-spanning-argument scaffold specified — before Mateo builds. She calls it a blocker.")


if __name__ == "__main__":
    run()
