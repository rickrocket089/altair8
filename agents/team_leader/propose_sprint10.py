"""Sophie stores the Sprint 10 proposal for Ingrid to review before the sprint opens.

Authored in sprint planning with the founder (2026-08-19), following the same
deliberate-logged-action pattern as set_north_star.py and
set_design_principles.py: the text is the founder-and-Sophie planning output,
this script is what makes it durable and reviewable rather than leaving it in
a chat log.

The sprint is NOT opened here. Ingrid reviews the design first -- the same
order used for Sprint 8, where the architecture was reviewed before any code
was written.
"""
import os

from agents.permissions import require_tool
from tools import db, vectorstore

PROPOSAL = """SPRINT 10 PROPOSAL -- Concept scenarios for the communication layer
Proposed by: Sophie Marchetti, sprint planning with the founder, 2026-08-19
Status: awaiting Ingrid's design review. Sprint not yet opened.

-------------------------------------------------------------------------------
1. WHY THIS SPRINT, AND WHY NOT THE OBVIOUS ONE
-------------------------------------------------------------------------------

The obvious Sprint 10 was Phase C: behavioural validation of Sprint 9's four
primitives against conventional forms. It is deferred, not dropped.

The founder's objection to building or validating next: we have never designed
alternatives. Sprints 8 and 9 designed implementations -- Mateo proposed an
architecture, Ingrid reviewed it before he built. No sprint has ever put
competing answers to "what is the communication layer" side by side. The team
has no mechanism that requires alternatives before construction.

A second objection from the founder, raised against Sophie's first draft of
this proposal and the reason it was rewritten: that draft seeded concept
generation with six starting points drawn from `candidate_approaches`. That
table's entry criterion is "Kenji found this in the literature." It is a
retrieval artifact. Seeding generation from it and then asking for novelty is
circular.

Supporting evidence that this is a structural pattern, not a one-off drafting
error: every concept this team has produced came from retrieval. Sprint 9's
four primitives came from Naledi surveying five adjacent fields. TVIR came
from a paper. The single non-derivative idea in the programme -- hypothesis #3,
control through iterative language rather than direct manipulation -- came from
the founder describing his own working practice. Concept generation is
currently a founder bottleneck, which is what the sixth agent was hired to
relieve, and handing her a reading list would reproduce it exactly.

-------------------------------------------------------------------------------
2. DSR PHASE
-------------------------------------------------------------------------------

The team is IN Design & Development and stays there. This is its design half,
which Sprints 8 and 9 skipped by going straight to construction. No phase
boundary is crossed, so no transition criterion is required under S10.

-------------------------------------------------------------------------------
3. SCOPE DECLARATION
-------------------------------------------------------------------------------

Applies to Pass 3 (Kenji's prior-art verification) only; Passes 1 and 2 are
generative, not literature work.

Coverage required (scope_checklist.py, 4 categories):
  - Third-party tools ............. YES, per concept, at verification depth only
  - Foundation-model-native ....... YES, per concept, at verification depth only
  - Open-source frameworks ........ YES, per concept, at verification depth only
  - Academic research ............. YES, per concept, at verification depth only

Exclusion with justification: this is a targeted per-concept prior-art check,
NOT a landscape scan. Kenji answers "has this specific concept been done, and
where" for each concept produced. He is not asked to survey a field. Retrieval
depth will be proportionate to that narrower claim and must be logged per S3.

-------------------------------------------------------------------------------
4. DESIGN -- THREE PASSES, ISOLATED AND ORDERED
-------------------------------------------------------------------------------

PASS 1 (Priya, blind). She receives:
  - the problem statement and North Star
  - the constraint set (section 5)
  - our own failure data from Sprints 6-8 (section 6)
  - team_leader/hypotheses and team_leader/design_principles

  She does NOT receive: the candidate_approaches list, TVIR, the Sprint 9
  primitives, or any other named prior art. She has no web_search by design.
  Output: concepts specified against the seven-field template (section 7).
  Stored at concept_designer/sprint10_concepts_blind, and preserved unmodified.

PASS 2 (Priya, sighted). Runs only after Pass 1 is stored. She is shown the
  candidate_approaches seeds and Sprint 9's primitives, and answers a narrow
  question: what do these add to, and what do they challenge in, what you
  already wrote? She may add concepts, revise concepts, or withdraw them --
  each change explicitly attributed to which seed caused it.
  Stored separately at concept_designer/sprint10_concepts_sighted.

PASS 3 (Kenji, verification). Per concept from both passes: has this been
  done, by whom, and how close is it. He never sees which pass a concept came
  from, so the verification is not biased by our interest in Pass 1.

Priya never scores her own novelty (enforced: no web_search in
agents/permissions.py). Kenji never generates concepts. Preserving Pass 1
before Pass 2 runs follows the same *_v1 preservation practice used for every
prior revision in this project.

-------------------------------------------------------------------------------
5. CONSTRAINT SET FOR PASS 1 (what she derives FROM)
-------------------------------------------------------------------------------

  - What the agent knows: the content, the audience, the communicative goal.
  - What the agent can emit: anything renderable in a browser. No slide, page,
    or chart-shaped assumption. Motion, interaction, zoom, dimensionality,
    non-linear structure are all available.
  - What the reader must be able to do: extract the intended point, and act on
    it, without the author present to narrate it.
  - No human authoring step sits between the agent and the artifact
    (hypothesis #1).
  - Human control is exercised through iterative natural language, not direct
    manipulation (hypothesis #3, currently deferred but live as a constraint).

-------------------------------------------------------------------------------
6. FAILURE DATA FOR PASS 1 (what she designs AGAINST)
-------------------------------------------------------------------------------

  - Medium-frame anchoring (GPT, Sprints 6-7): audience-sensitive reasoning
    trapped inside a "which chart" frame that never asks whether any chart is
    the right medium.
  - Form-conservatism (Gemini, Sprint 6): candidate pattern only; did not
    strongly replicate under adversarial pressure in Sprint 7. Weak evidence,
    carried as a hypothesis not a finding.
  - Form-as-signal reasoning (Claude, Sprint 7): the positive case -- choosing
    a form because a chart would send the wrong communicative register.
  - Confabulated content passing structural validation (Sprint 8, run 1): a
    chart with correct field names and entirely off-topic data. Root cause was
    a data-flow gap between pipeline stages, not model incapability.
  - Structural validity does not imply content correctness (Sprint 8): the
    architecture's stage separation caught a syntax failure and missed a
    content failure completely.
  - The culturally-scripted-scenario problem (Naledi, Sprint 7): recognisable
    professional scripts can be pattern-matched rather than reasoned from.

-------------------------------------------------------------------------------
7. SEVEN-FIELD SCENARIO TEMPLATE (per concept, both passes)
-------------------------------------------------------------------------------

  1. What would we build -- one paragraph, concrete enough to picture.
  2. How would it work -- the actual mechanism. What the agent decides, what
     it generates, what the reader does, in what order.
  3. Why is it new -- the claim, stated so Kenji can check it.
  4. Why could it solve OUR problem -- tied to audience + goal -> form.
  5. How new is it -- her graded estimate, flagged as pending verification.
  6. What would falsify it -- the cheapest experiment that would show it does
     not work. "I cannot name one" is a permitted and informative answer.
  7. Which hypotheses or design principles it serves or breaks -- violations
     named, never designed around silently.

-------------------------------------------------------------------------------
8. THE KNOWN WEAKNESS IN THIS DESIGN, STATED UP FRONT
-------------------------------------------------------------------------------

Priya cannot actually be blind to prior art. Her base model has read the
visualization literature in pretraining. Withholding the seed list withholds
retrieval, not knowledge.

So Pass 1 does not test "can concepts be generated uncontaminated by prior
art." That experiment is not available to us with an LLM. What it tests is
narrower and still worth testing: whether EXPLICIT SEEDING pulls the output
toward the seeds. Pass 1 versus Pass 2 measures the pull of the reading list,
not the absence of influence. Every claim made about this sprint's results must
respect that boundary, and any framing that implies otherwise is wrong.

-------------------------------------------------------------------------------
9. SUCCESS CRITERIA (falsifiable, per Ingrid's Sprint 8 requirement)
-------------------------------------------------------------------------------

The sprint succeeds if:
  a. Pass 1 yields at least 3 concepts complete across all seven fields.
  b. Each concept's falsification test (field 6) is judged buildable by Mateo
     within roughly one sprint. A concept nobody can test is not a deliverable.
  c. Kenji returns a prior-art verdict for every concept from both passes.
  d. The founder can make an actual choice from the comparison -- the output
     is a decision input, not a reading list.

The sprint FAILS informatively if Pass 1 comes back thin or derivative anyway.
That result would say the constraint set built over nine sprints is not yet
rich enough to derive from, which is a real finding about our own foundations
and would change what Sprint 11 should be.

-------------------------------------------------------------------------------
10. EXPLICITLY NOT IN SCOPE
-------------------------------------------------------------------------------

  - Building any concept (that is Sprint 11 at the earliest).
  - Phase C validation of Sprint 9's four primitives (deferred, still owed).
  - Choosing a winner. This sprint produces the comparison; the founder
    chooses, as with every prior direction decision.

-------------------------------------------------------------------------------
11. OPEN QUESTIONS FOR THE REVIEWER
-------------------------------------------------------------------------------

  - Is blind-then-sighted a sound design or procedural theatre, given
    section 8?
  - Is the seven-field template rigorous enough to be worth filling in, or
    does it invite fluent specification of unbuildable things?
  - Is novelty the right thing to grade at all? Novelty is cheap; being wrong
    is novel. Does field 5 risk optimising for the wrong target?
  - Is the constraint set (section 5) rich enough to derive from, or is it so
    thin that Pass 1 is set up to fail?
  - What procedurally verifies that Pass 1 was genuinely run blind?
"""


def run() -> None:
    require_tool("team_leader", "route_task")
    db.set_memory("team_leader", "status", "online")

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Review: Sprint 10 design (blind-then-sighted concept generation)",
        description=(
            "Sprint 10 proposal stored for design review before the sprint opens. "
            "Same order as Sprint 8: design reviewed before work starts."
        ),
    )

    db.set_memory("team_leader", "sprint10_proposal", PROPOSAL)
    vectorstore.remember(
        collection_name="team_leader_memory",
        doc_id=f"sprint10-proposal-task-{task_id}",
        text=PROPOSAL,
        metadata={"agent": "team_leader", "type": "sprint_proposal", "sprint": 10},
    )
    db.update_task(
        task_id,
        status="pending",
        result=None,
        artifact_type="sprint_proposal",
        artifact_payload={"memory_key": "team_leader/sprint10_proposal", "sprint": 10},
    )

    print(f"[Sophie Marchetti] Sprint 10 proposal stored "
          f"(team_leader/sprint10_proposal), task {task_id} open for Ingrid.")
    print(f"[Sophie Marchetti] {len(PROPOSAL)} chars. Sprint NOT opened — "
          f"awaiting design review.")


if __name__ == "__main__":
    run()
