"""Sprint 15: Priya generates 3-5 concepts for a visualization-knowledge
layer, centered on Candidate Approach #11, optionally combined with #1
(TVIR) and #2 (Structured Visualization Design Knowledge).

Different shape of "blind" than Sprint 10's Pass 1: there, Priya was kept
from ALL prior art so concepts derived from the team's own constraints
rather than a reading list. Here, the prior art (specifically #1/#2/#11)
IS the point -- Sophie's brief centers the sprint on #11. What she is
blind to is any steer toward a "best" implementation: no one has told
her which of the 5 sketch-level directions Sophie floated in chat to
prefer, and Kenji's reality-check pass runs strictly AFTER hers, not
before. Same "evidenced, not asserted" discipline as Sprint 10 --
this script logs exactly what was and wasn't in her input before the
call, for Ingrid's inspection gate.

Per Candidate #11's own on-record history (read in full below, not
summarized away): this idea returned for a second time after the
founder raised and dropped a version of it in August. The BINDING
OBJECTION that survived that history is real and given to Priya
verbatim -- a corpus of existing artifacts records what people DID, not
what WORKED, and if Hypothesis 6 holds, the missing dimension is
audience/goal, which no existing corpus is labeled by. Concepts that
don't engage this objection are not doing the assigned task.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.concept_designer.persona import NAME, SYSTEM_PROMPT
from agents.permissions import require_tool
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"

SOURCES_READ = [
    "team_leader/sprint15_input_brief_for_priya (hard constraints, do-nots, template)",
    "candidate_approaches #1 (TVIR), #2 (Structured Visualization Design Knowledge), "
    "#11 (Corpus as knowledge structure) -- full descriptions, including #11's own "
    "binding objection and history",
    "Sprint 14 summary (FVBS/NOT-IN-SET findings, one page, no raw data)",
    "the controlled audience/goal vocabulary (6x6), as a possible schema element",
]
EXCLUDED_BY_DESIGN = [
    "The other 9 candidate approaches (#3-#10, #12) -- sprint is deliberately scoped to #11/#1/#2",
    "Sophie's own 5 sketch-level concept directions from the chat that scoped this sprint "
    "(Case Library, Rule/Constraint Graph, Taxonomy+Rubric, Design Programs, Embedding-Ontology) "
    "-- these were floated as illustrative range only, not read into this call, so Priya is not "
    "anchored on Sophie's own first guesses",
    "Sprint 14 raw data/scores (only the summary, not blind_scorer/kenji memory keys)",
    "Kenji's reality-check pass (runs strictly after this one, per the brief's process)",
]

SPRINT14_SUMMARY = """SPRINT 14 SUMMARY (one page, for grounding only -- not a
literature review):

Sprint 14 tested whether models choose the AUDIENCE-OPTIMAL visualization
form, not just a structurally valid one (form-valid-but-suboptimal, FVBS,
criterion). Real result: among structurally valid trials across 18
scenarios x 3 models x 2 conditions, models chose the audience-optimal
(Registrar-ranked #1) form only 46.1% of the time -- FVBS rate 53.9%,
within the pre-registered 40-65% band. This CONFIRMS that audience-goal
sensitivity and audience-OPTIMAL form selection are distinct
competencies: models are structurally competent but not reliably
audience-optimal. The mechanism behind this gap -- internalized
structure that could be elicited better, versus fluent reproduction of
convention -- remains genuinely unresolved; that is what this sprint's
knowledge-layer concepts are meant to help address, one way or another.

Secondary finding: 26.7% of trials produced NOT-IN-SET outcomes (models
nominating a form outside the tool-generated candidate set), well above
the 5-20% prediction. Verified causes: (a) a REAL vocabulary ceiling --
models reach for forms (dumbbell/connected-dot, violin, raincloud,
beeswarm, KDE density plots) that the candidate-generation tool (Draco,
7 basic mark types: point/bar/line/area/text/tick/rect) cannot express
at all; (b) the tool's own cost-ranking sometimes excludes a valid
candidate from consideration; (c) one scoring-pipeline bug (now fixed).
Cause (a) is real and substantive -- it means the vocabulary problem is
not just "which form is optimal" but "which forms are even in the
tool's vocabulary to rank in the first place."
"""

AUDIENCE_GOAL_VOCAB = """CONTROLLED AUDIENCE x GOAL VOCABULARY (6x6), as a possible schema element:

AUDIENCE:
A1 - familiar with the measurement domain, unfamiliar with this specific dataset
A2 - no domain vocabulary, accustomed to everyday quantitative comparisons
A3 - monitors this metric repeatedly, holds a stable mental model, task is anomaly detection
A4 - acts on a single viewing, under time pressure, no follow-up questions possible
A5 - holds a strong prior belief, will scrutinize for confirming/disconfirming evidence
A6 - receives the chart embedded in a document, forms first interpretation from chart alone

GOAL:
G1 - establish whether a directional change over time is monotonic, interrupted, or cyclical
G2 - determine which discrete category has the largest/smallest value on a measure
G3 - understand how values are distributed across a full range
G4 - support a binary/multi-option choice, make the decision-relevant difference immediate
G5 - identify whether variables move together, independently, or in opposition
G6 - verify whether a value falls within or outside a pre-specified acceptable range
"""

CANDIDATE_1_RECORD = """CANDIDATE #1 -- TVIR: Building Deep Research Agents Towards
Text-Visual Interleaved Report Generation
Closest structural analog found to date -- multi-agent pipeline generating
reports with interleaved text/charts/images. Confirmed via detailed read:
visual placement/type is description-driven heuristic, not goal-to-form
reasoning; no audience model. Its real novel contribution is orthogonal to
our question: a "decorative vs evidential" visual grounding metric
(Chart-Source Consistency). Full working implementation confirmed
(github.com/NJU-LINK/TVIR, Apache 2.0): agent/ (planning, image search,
chart generation, writing agents), benchmark/ (100 expert-curated tasks),
Python 3.12, Claude/Qwen/GLM support, E2B sandbox for execution."""

CANDIDATE_2_RECORD = """CANDIDATE #2 -- Structured Visualization Design Knowledge for
Grounding Generative Reasoning and Situated Feedback
Closer to our content-to-form gap than LLM4Vis itself -- proposes structured
design knowledge as a grounding layer for generative reasoning, addressing
the DracoGPT-identified tension between rigid symbolic constraint systems
and flexible-but-ungrounded LLM generation."""

CANDIDATE_11_RECORD = """CANDIDATE #11 -- Corpus of existing business-communication
artifacts as a knowledge structure for form selection
Founder proposal. Thousands of decks, templates and visualization libraries
exist (slidemodel.com and similar). Use them to teach models what a given
visualization asserts and when it should be used, held in a knowledge graph
or comparable structure.

HISTORY -- this is the second time. The founder raised a version of this on
2026-08-06 (scraped semantic library mapping content to visualization).
Sophie advised against it then on the grounds that it anchors the system on
legacy 2D formats and undercuts design principle 4; the founder agreed and
it became Sprint 9 (survey adjacent fields instead). That it has returned is
itself information -- the underlying need is real and Sprint 9 did not meet
it.

WHAT IS DIFFERENT THIS TIME: the framing. August was a retrieval library to
generate FROM. September is a source of evidence about what forms MEAN and
when they apply. These are not the same proposal and the August objection
does not automatically transfer.

THE BINDING OBJECTION, which does transfer: a corpus of existing decks
records what people DID, not what WORKED. There is no outcome variable
anywhere in it. Sprint 2's finding was that these tools automate production
while leaving communication reasoning untouched; a corpus of their output
teaches production, i.e. the ceiling this project exists to break.

THE VERSION THAT SURVIVES: a corpus is a strong source for the CONVENTION
PRIOR -- what the canonical form for a given data job is -- which is
exactly what Sprint 7's adversarial pairs had to establish before they
could test an override. Knowing the norm is a precondition for knowing when
the norm is wrong. Convention prior, not target.

THE QUESTION THAT DECIDES IT: what would be in such a graph that is not
already in the model's weights? Conventions are heavily represented in
training data. If hypothesis 6 holds, the missing dimension is audience and
goal, not canonical form -- and no existing corpus is labelled by audience
or goal. Backlog #23 discriminates between these before anything is built.

Also unresolved: licensing of commercial template libraries.

ADDENDUM (Sprint 12 close): Bangalore & Stent (2007) found individually-
trained sentence-planning models transfer near-chance to other users
(RankLoss <= 0.52 vs 0.50 baseline) -- domain-level adaptation generalizes
far better than individual-level. Concrete design signal for this candidate
if it's ever built: a convention-prior corpus should be scoped at the
domain/genre level, not attempt to capture individual-author idiosyncrasy --
the latter appears to not transfer at all.

ADDENDUM (Sprint 13 close): Sprint 13's real result reactivates this
candidate with a concrete argument. The rerun needs a ranked audience-
optimal ordering of forms per audience x goal pairing -- exactly the gap
Draco's constraint vocabulary cannot fill (it has no audience-model terms).
A corpus of existing communication artifacts, read as a convention prior
per this candidate's own "survives" framing (not as a generation target),
is one real way to supply that ranking data. Disposition changed from the
prior triage (conditional) to ACTIVE.

ADDENDUM (Sprint 14 close, 2026-09-16): Sprint 14 confirmed models fail
audience-optimality on ~54% of structurally-valid trials, AND found a real
vocabulary ceiling (26.7% NOT-IN-SET, partly caused by models reaching for
form families -- violin, raincloud, beeswarm, dumbbell -- that the
candidate-generation tool cannot express at all). This is a second, distinct
argument for this candidate beyond the ranking-data gap: a corpus could also
be a source of FORM VOCABULARY the current tooling lacks, not just audience-
fit rankings. Both arguments need engaging, not just the ranking one."""

TEMPLATE = """For EACH concept (3-5 total), give all eight fields, in this order:

1. NAME + ONE-SENTENCE THESIS.
2. REPRESENTATION -- what is the data structure? (cases, rules, programs,
   ontology+embeddings, or something else entirely -- do not default to
   the obvious answer without considering alternatives.)
3. FEEDING -- sources + extraction mechanism (manual curation, LLM-
   assisted labeling, parsing, some combination). Be concrete about
   where the first real content comes from, not just "a corpus."
4. UPDATE -- how does it grow? (versioning, QA, drift -- a one-time
   curated handbook is a failure mode, say how this avoids that.)
5. RUNTIME USE -- how does it act on generation? (retrieve exemplars /
   constrain search / plan steps / evaluate candidates / something else)
6. HOW IT ADDRESSES THE SPRINT 14 CEILING -- which failure modes (FVBS,
   NOT-IN-SET, or both) does it directly mitigate, and how specifically?
7. FALSIFIER -- what would quickly devalue this concept? Concretely
   testable -- what would you observe, measure, and what threshold
   counts as failure.
8. RISKS -- 3 bullets, MUST include an explicit answer to Candidate
   #11's own binding objection: does this concept risk reinforcing
   convention (teaching what people DID, not what WORKS for a specific
   audience/goal) rather than breaking the ceiling? If a concept doesn't
   have a real answer to this, say so plainly rather than talking around it."""


def build_user_message(brief: str) -> str:
    return f"""Sprint 15. You are generating concepts for a VISUALIZATION-
KNOWLEDGE LAYER -- centered on Candidate Approach #11 (a corpus of
existing business-communication artifacts as a knowledge structure for
form selection), optionally combined with Candidate #1 (TVIR) and
Candidate #2 (Structured Visualization Design Knowledge).

This is not a blank-slate concept sprint like Sprint 10 -- the direction
is already chosen (the founder's explicit call, after strategic review
of where Sprints 13/14 had and hadn't moved the project forward). Your
job is to work out WHAT KIND of knowledge layer this could concretely
be: 3-5 clearly distinct answers to "how is visualization knowledge
represented, and how do we feed it."

{brief}

{SPRINT14_SUMMARY}

{AUDIENCE_GOAL_VOCAB}

=== CANDIDATE APPROACHES -- FULL RECORDS, READ CAREFULLY ===
Candidate #11 is the center of this sprint. It carries real, on-record
objections and a "version that survives" framing from the team's own
prior debate. Your concepts must engage this history, not ignore it --
especially the BINDING OBJECTION (a corpus of existing decks records
what people DID, not what WORKED) and THE QUESTION THAT DECIDES IT
(what would be in such a knowledge structure that is not already in the
model's weights -- if Hypothesis 6 holds, the missing dimension is
audience and goal, which no existing corpus is labeled by). Candidates
#1 and #2 are optional combination material, not mandatory ingredients.

{CANDIDATE_1_RECORD}

{CANDIDATE_2_RECORD}

{CANDIDATE_11_RECORD}

{TEMPLATE}

Before the concepts, write a short section titled HOW I APPROACHED THIS.
After them, write WHERE I AM LEAST CONFIDENT -- which concept you would
bet against, and why. Be specific, this is used, not filed."""


def run() -> None:
    require_tool("priya", "write_concept_scenario")
    db.set_memory("priya", "status", "online")

    brief = db.get_memory("team_leader", "sprint15_input_brief_for_priya") or ""
    if not brief:
        raise SystemExit("Missing team_leader/sprint15_input_brief_for_priya -- run open_sprint15.py first.")

    user_message = build_user_message(brief)

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="priya",
        title="Sprint 15: generate 3-5 knowledge-layer concepts (#11-first)",
        description="Concepts only, no prototype. Must engage #11's binding objection.",
    )

    input_log = f"""SPRINT 15 -- COMPLETE INPUT LOG
Written for Ingrid's inspection gate before the reality-check pass runs.

MODEL: {MODEL}
TASK ID: {task_id}

DATA SOURCES READ FROM STORAGE:
{chr(10).join('  - ' + s for s in SOURCES_READ)}

EXCLUDED BY DESIGN (not read, not passed):
{chr(10).join('  - ' + s for s in EXCLUDED_BY_DESIGN)}

CONTEXT-CARRY CONFIRMATION: single stateless Anthropic API call. No
vectorstore query in this run. No prior-turn context, no shared-memory
injection beyond the sources listed above. The complete input the model
received is the system prompt and user message reproduced verbatim below.

================================================================================
SYSTEM PROMPT (verbatim)
================================================================================
{SYSTEM_PROMPT}

================================================================================
USER MESSAGE (verbatim)
================================================================================
{user_message}
"""
    db.set_memory("priya", "sprint15_input_log", input_log)
    print(f"[{NAME}] Input log written ({len(input_log)} chars) -> priya/sprint15_input_log")

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model=MODEL, max_tokens=16000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        response = stream.get_final_message()

    concepts = response.content[0].text
    db.log_usage("priya", response.usage.input_tokens, response.usage.output_tokens)
    if response.stop_reason == "max_tokens":
        concepts += "\n\n[TRUNCATED -- hit max_tokens, incomplete.]"

    db.set_memory("priya", "sprint15_concepts", concepts)
    vectorstore.remember(
        collection_name="concept_designer_memory",
        doc_id=f"sprint15-concepts-task-{task_id}",
        text=concepts,
        metadata={"agent": "priya", "type": "concept_scenarios", "sprint": 15},
    )
    db.update_task(
        task_id, status="completed", result=concepts,
        artifact_type="concept_scenarios",
        artifact_payload={
            "memory_key": "priya/sprint15_concepts",
            "input_log_key": "priya/sprint15_input_log",
        },
    )

    print(f"[{NAME}]\n\n{concepts}")
    print(f"\n\n--- {len(concepts)} chars, stored as priya/sprint15_concepts ---")


if __name__ == "__main__":
    run()
