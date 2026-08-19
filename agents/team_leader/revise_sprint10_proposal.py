"""Sophie revises the Sprint 10 proposal against Ingrid's design review.

Applies all 7 blocking items from ingrid/sprint10_design_review. Same pattern
as revise_landscape_scan.py and revise_behavioral_reasoning_test.py: the
original is preserved at a _v1 key and the revision becomes the current
version.

Guard against the Sprint 6 Gemini bug: the _v1 preservation only writes if
_v1 does not already exist, so a second run cannot overwrite the clean
original with an already-revised version.

Ingrid's recommended (non-blocking) items 8, 9 and 10 are deliberately NOT
applied here -- the founder authorised the 7 blocking items. They remain open.
"""
import os

from agents.permissions import require_tool
from tools import db, vectorstore

PROPOSAL_V2 = """SPRINT 10 PROPOSAL (v2) -- Concept scenarios for the communication layer
Proposed by: Sophie Marchetti, sprint planning with the founder, 2026-08-19
Revised 2026-08-19 against Ingrid's pre-execution design review
(ingrid/sprint10_design_review, verdict: revise the design first).
Status: awaiting Ingrid's confirmation. Sprint not yet opened.

CHANGES IN v2: applies all 7 blocking items -- field 3 grounding instruction
(1), Pass 1 input logging (2), field 5 replaced with 5a/5b (3), goal space
added to the constraint set (4), field 6 measurement instruction (5), Phase C
dependency named (6), Pass 4 synthesis step added (7). Also adds the PROCESS
REVIEW STATUS block Ingrid flagged as missing (item 12) and bounds Mateo's
buildability check per her finding 8. Ingrid's recommended items 8, 9 and 10
are NOT applied and remain open.

-------------------------------------------------------------------------------
0. PROCESS REVIEW STATUS
-------------------------------------------------------------------------------

Last Sprint Review covered: Sprints 6-9 (process_reviews id=3, Ingrid)
Sprints since last review:  0
Sprint Review due this sprint? No -- due at Sprint 12 (cadence: every 3).

Verified against the `process_reviews` table directly at planning time:
#1 covers sprints 1-5, #2 covers sprints 6-9.

-------------------------------------------------------------------------------
1. WHY THIS SPRINT, AND WHY NOT THE OBVIOUS ONE
-------------------------------------------------------------------------------

The obvious Sprint 10 was Phase C: behavioural validation of Sprint 9's four
primitives against conventional forms. It is deferred, not dropped. See
section 10 for the cost of that deferral, now named explicitly.

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

Applies to Pass 3 (Kenji's prior-art verification) only; Passes 1, 2 and 4 are
generative or synthetic, not literature work.

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
4. DESIGN -- FOUR PASSES, ISOLATED AND ORDERED
-------------------------------------------------------------------------------

PASS 1 (Priya, blind). She receives:
  - the problem statement and North Star
  - the constraint set (section 5), including the goal space
  - our own failure data from Sprints 6-8 (section 6)
  - team_leader/hypotheses and team_leader/design_principles

  She does NOT receive: the candidate_approaches list, TVIR, the Sprint 9
  primitives, or any other named prior art. She has no web_search by design.
  Output: concepts specified against the template in section 7.
  Stored at concept_designer/sprint10_concepts_blind, preserved unmodified.

  BLINDNESS IS EVIDENCED, NOT ASSERTED (Ingrid item 2). Before Pass 2 may
  begin, Sophie must log, in full and readable form:
    (a) the complete system prompt and user message sent to Priya for Pass 1,
        stored at concept_designer/sprint10_pass1_input -- the actual text, not
        a summary, so the absence of candidate_approaches, TVIR, the Sprint 9
        primitives and any other named prior art is verifiable by inspection;
    (b) a written confirmation that no context-carry mechanism (shared memory
        injection, vectorstore retrieval over prior sprint outputs, prior-turn
        context) contributed excluded material to that call, naming what was
        checked.
  Ingrid confirms (a) and (b) before Pass 2 runs. Rationale, in her words:
  blindness is a property of the input the model actually received, not of the
  orchestrator's intent. This project has twice found rules that existed
  without enforcement; this one is enforced by inspectable evidence.

PASS 2 (Priya, sighted). Runs only after Pass 1 is stored AND Ingrid has
  confirmed the Pass 1 input log. She is shown the candidate_approaches seeds
  and Sprint 9's primitives, and answers a narrow question: what do these add
  to, and what do they challenge in, what you already wrote? She may add,
  revise or withdraw concepts -- each change explicitly attributed to which
  seed caused it. Stored at concept_designer/sprint10_concepts_sighted.

PASS 3 (Kenji, verification). Per concept from both passes: has this been
  done, by whom, and how close is it. He is not told which pass a concept came
  from. Retrieval log per S3.

PASS 4 (Sophie, synthesis) -- NEW in v2, per Ingrid item 7. The three passes
  produce concepts, revisions and verdicts; none of them produces the decision
  input this sprint promises. Sophie assembles them into a single comparative
  format for the founder. Hard constraint: NO NEW CLAIMS. Pass 4 may only
  restate, organise and compare what Passes 1-3 actually produced. Any
  observation of Sophie's own must be labelled as such and kept separate from
  the concepts and verdicts. Format is fixed before the sprint runs: one row
  per concept, columns for each template field plus Kenji's verdict, followed
  by a plain-language comparison of where the concepts genuinely differ.
  This is the step where this project has historically overclaimed in
  synthesis; the constraint exists because of that history.

Priya never scores her own external novelty (enforced: no web_search in
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

  THE GOAL SPACE (Ingrid item 4). The communicative goal may be to persuade,
  to inform, to align, or to report -- these are different jobs and a form
  that serves one may fail another. The audience may be a single decision-
  maker, a working team, or a broader distributed group who will encounter the
  artifact without context. The artifact must work without its author present
  to narrate it, whichever combination applies. Concepts should state which
  region of this space they serve; a concept that claims to serve all of it
  must justify that claim rather than assume it.

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
7. SCENARIO TEMPLATE (per concept, both generative passes)
-------------------------------------------------------------------------------

  1. What would we build -- one paragraph, concrete enough to picture.

  2. How would it work -- the actual mechanism. What the agent decides, what
     it generates, what the reader does, in what order.

  3. Why is it new -- the claim, stated so Kenji can check it.
     PASS 1 CONSTRAINT (Ingrid item 1): in Pass 1 this must be justified
     against the constraint set and failure data you were given, NOT against
     named existing approaches, tools or papers. You have not been given a
     prior-art list and must not write as though you had. Claims of the form
     "unlike [named system]" belong to Pass 2, not Pass 1.

  4. Why could it solve OUR problem -- tied to audience + goal -> form, and
     stating which region of the goal space (section 5) it serves.

  5a. GROUNDEDNESS (replaces novelty self-grading, Ingrid item 3) -- what in
      the constraint set or failure data does this concept directly respond to?
      Name it specifically. A concept that cannot answer this is floating free
      of the brief and should be flagged as such, not defended.

  5b. DISTINCTIVENESS WITHIN THIS PASS -- in what specific way does this
      concept occupy different ground from the others you produced? This is
      about spanning the solution space, not about being unusual.

      (Field 5's original "how new is it" self-grading is deleted. Rationale,
      Ingrid's: self-graded novelty creates structural pressure toward
      exotic-but-wrong -- low-novelty grades read as weak output, so the
      incentive is to reframe familiar mechanisms in unfamiliar language.
      External novelty is Kenji's job in Pass 3 and does not need anticipating.)

  6. What would falsify it -- the cheapest experiment that would show this does
     not work. REQUIRED FORM (Ingrid item 5): state what you would observe,
     what you would measure, and what threshold of that measurement counts as
     failure. "I cannot name one" remains a permitted and informative answer.
     "Users might struggle" does not pass -- it names no observation, no
     measure and no threshold.

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
toward the seeds.

WHAT A PASS 1 / PASS 2 DIFFERENCE LICENSES (Ingrid's boundary, adopted
verbatim in substance):
  Licensed:     "explicit seeding shifted the conceptual output in these
                 specific directions"
  Licensed:     "Pass 1 was generated without the seed list; Pass 2 shows what
                 the seeds add or displace"
  NOT licensed: "Pass 1 concepts are novel" -- they may be convergent with the
                 literature through pretraining rather than through the seeds
  NOT licensed: "Priya's generation is independent of prior art"
  NOT licensed (on finding NO difference): "the seed list contains no new
                 information" -- it may mean pretraining exposure is
                 comprehensive enough that explicit seeding adds nothing

No claim about the absolute novelty of Pass 1 concepts is licensed by this
design. Any output of this sprint that implies otherwise is wrong and must be
corrected before it reaches the website or the founder's public writing.

-------------------------------------------------------------------------------
9. SUCCESS CRITERIA (falsifiable, per Ingrid's Sprint 8 requirement)
-------------------------------------------------------------------------------

The sprint succeeds if:
  a. Pass 1 yields at least 3 concepts complete across all template fields.
  b. Each concept's falsification test (field 6) is judged buildable by Mateo
     within roughly one sprint. BOUNDED (Ingrid finding 8): Mateo reviews
     field 6 only, not the full template, and returns a binary verdict --
     buildable / not buildable within one sprint -- plus one sentence of
     reasoning. A test requiring infrastructure the team has not built counts
     as buildable only if that infrastructure could be built inside the same
     sprint. Full architectural engagement happens only if a concept is chosen.
  c. Kenji returns a prior-art verdict for every concept from both passes.
  d. Pass 4 produces the comparative format, and the founder can make an actual
     choice from it.

The sprint FAILS informatively if Pass 1 comes back thin or derivative anyway.
That result would say the constraint set built over nine sprints is not yet
rich enough to derive from, which is a real finding about our own foundations
and would change what Sprint 11 should be.

-------------------------------------------------------------------------------
10. EXPLICITLY NOT IN SCOPE
-------------------------------------------------------------------------------

  - Building any concept (that is Sprint 11 at the earliest).
  - Choosing a winner. This sprint produces the comparison; the founder
    chooses, as with every prior direction decision.
  - Phase C validation of Sprint 9's four primitives (deferred, still owed).

  PHASE C DEPENDENCY, NAMED (Ingrid item 6). Deferring Phase C again means
  Sprint 10's concepts are generated against Sprint 9 primitives that remain
  unvalidated claims. If Phase C later shows one of those four primitives is
  wrong or context-limited, any Sprint 10 concept that depends on it will need
  revision. This dependency is accepted deliberately by the team, not
  overlooked. The public Sprint 9 results page, which named Phase C as Sprint
  10, is being corrected to state the deferral rather than left to stand.

-------------------------------------------------------------------------------
11. OPEN ITEMS NOT APPLIED IN v2
-------------------------------------------------------------------------------

Ingrid's recommended (non-blocking) items remain open, founder's call:
  8.  Tell Priya explicitly that the browser is the current implementation
      medium, and to name any gap between the ideal form and what is
      browser-renderable today.
  9.  Add a self-identification field to Kenji's Pass 3 verdict ("could I tell
      which pass this came from? yes/no/probably"), as data on how far the two
      passes differ at the framing level.
  10. Add a positive success criterion to the template -- what could a human do
      that they cannot do now, and how would we know -- distinct from field 6's
      falsification test.

Separately flagged by Sophie, not from Ingrid's list: Ingrid's review asserted
she had cross-checked the process-review count via `tools/db.py` directly. She
had not -- the reviewer scripts pass her text, not a database connection. Her
conclusion was correct, but the verification was rhetorical. The persona
instruction added after Process Review #2 ("independently verify Sophie's
stated count against the DB") is not executable as written and currently
produces confabulated compliance. This needs either real query results passed
into her review prompts, or removal of the instruction. Logged for decision;
not part of this sprint's scope.
"""


def run() -> None:
    require_tool("team_leader", "route_task")
    db.set_memory("team_leader", "status", "online")

    existing_v1 = db.get_memory("team_leader", "sprint10_proposal_v1")
    if not existing_v1:
        original = db.get_memory("team_leader", "sprint10_proposal")
        if not original:
            raise SystemExit("No sprint10_proposal found to revise.")
        db.set_memory("team_leader", "sprint10_proposal_v1", original)
        print("[Sophie Marchetti] Original preserved at team_leader/sprint10_proposal_v1")
    else:
        print("[Sophie Marchetti] _v1 already exists — not overwriting (rerun-safe).")

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Confirm: Sprint 10 proposal v2 (7 blocking items applied)",
        description="Revision of the Sprint 10 design against ingrid/sprint10_design_review.",
    )

    db.set_memory("team_leader", "sprint10_proposal", PROPOSAL_V2)
    vectorstore.remember(
        collection_name="team_leader_memory",
        doc_id=f"sprint10-proposal-v2-task-{task_id}",
        text=PROPOSAL_V2,
        metadata={"agent": "team_leader", "type": "sprint_proposal", "sprint": 10, "version": 2},
    )
    db.update_task(
        task_id, status="pending", result=None,
        artifact_type="sprint_proposal",
        artifact_payload={"memory_key": "team_leader/sprint10_proposal", "sprint": 10, "version": 2},
    )

    print(f"[Sophie Marchetti] v2 stored ({len(PROPOSAL_V2)} chars), task {task_id} "
          f"open for Ingrid's confirmation. Sprint still NOT opened.")


if __name__ == "__main__":
    run()
