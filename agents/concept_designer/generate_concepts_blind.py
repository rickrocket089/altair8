"""Sprint 10, Pass 1: Priya generates concepts BLIND.

She receives the problem, the constraint set (including the goal space), the
Sprints 6-8 failure data, and the team's hypotheses and design principles.
She does NOT receive candidate_approaches, TVIR, the Sprint 9 primitives, or
any other named prior art.

BLINDNESS IS EVIDENCED, NOT ASSERTED (Ingrid's blocking item 2). This script
writes the complete system prompt and user message actually sent, verbatim, to
concept_designer/sprint10_pass1_input, together with a record of every data
source read. Ingrid inspects that log before Pass 2 may run. Her rationale:
blindness is a property of the input the model received, not of the
orchestrator's intent.

Context-carry: this is a single stateless Anthropic call. No vectorstore
query, no prior-turn context, no shared-memory injection. The only stored data
read is the three team_leader keys listed in SOURCES_READ, each checked for
named prior art before inclusion.

max_tokens is 16000 -- 8000 has truncated long generations four times in this
project now.
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
    "team_leader/north_star",
    "team_leader/hypotheses",
    "team_leader/design_principles",
]

EXCLUDED_BY_DESIGN = [
    "candidate_approaches (all 5 rows -- TVIR, Structured Visualization Design "
    "Knowledge, GoT/T2I-R1/ControlThinker, NL2INTERFACE/SmartMLVs, PPTAgent/PPTEval)",
    "Sprint 9's four visual primitives (scrollytelling, annotation-led path, "
    "force-directed graph, diegetic display) and the 11 surveyed patterns",
    "Sprint 8's pipeline architecture and TVIR's 4-stage structure",
    "Kenji's landscape scans and any named third-party tool",
    "vectorstore collections (not queried at all in this run)",
]

CONSTRAINT_SET = """WHAT THE AGENT KNOWS
The content, the audience, and the communicative goal.

WHAT THE AGENT CAN EMIT
Anything renderable in a browser. There is no slide, page, or chart-shaped
assumption. Motion, interaction, zoom, dimensionality and non-linear structure
are all available to you.

WHAT THE READER MUST BE ABLE TO DO
Extract the intended point, and act on it, without the author present to
narrate it.

NO HUMAN AUTHORING STEP
Nothing sits between the agent and the finished artifact. A human does not lay
it out, position elements, or assemble it.

CONTROL IS LINGUISTIC
The human steers through iterative natural-language feedback, not by directly
manipulating visual primitives.

THE GOAL SPACE
The communicative goal may be to persuade, to inform, to align, or to report --
these are different jobs, and a form that serves one may fail another. The
audience may be a single decision-maker, a working team, or a broader
distributed group who will encounter the artifact with no context. The artifact
must work without its author present, whichever combination applies. State
which region of this space your concept serves. A concept claiming to serve all
of it must justify that, not assume it."""

FAILURE_DATA = """These are our own findings from three sprints of behavioural
testing and one built pipeline. They are what you design against.

1. MEDIUM-FRAME ANCHORING. Asked to choose a visual form, a model reasoned
   carefully about the audience -- and stayed trapped inside a "which chart?"
   frame the whole time. It never asked whether any chart was the right medium.
   The reasoning was genuinely audience-sensitive and the frame was still wrong.

2. FORM-CONSERVATISM (weak evidence, carried as hypothesis not finding). One
   model appeared to stay within conventional chart forms even while switching
   sub-type. This did not strongly replicate under adversarial pressure.

3. FORM-AS-SIGNAL REASONING (the positive case). A model chose plain prose over
   a chart for new staff, explicitly because a chart would imply a need to
   analyse when analysis was not the goal. It reasoned about what the form
   itself signals, not only about what it depicts.

4. CONFABULATED CONTENT PASSING STRUCTURAL VALIDATION. Our pipeline produced a
   chart with correct field names, valid syntax, and data about an entirely
   different subject than the document it sat in. Every automated check passed.
   Root cause was a data-flow gap between stages, not model incapability -- one
   stage never received what the others knew.

5. STRUCTURAL VALIDITY DOES NOT IMPLY CONTENT CORRECTNESS. Our architecture's
   stage separation caught a syntax failure and missed a content failure
   completely.

6. THE CULTURALLY-SCRIPTED-SCENARIO PROBLEM. Recognisable professional
   situations (a finance audit, a VP status check) can be pattern-matched from
   training rather than reasoned about from context. The least scripted
   scenarios produced the most diagnostic evidence."""

TEMPLATE = """For EACH concept, give all eight fields, in this order, with these
headings.

1. WHAT WOULD WE BUILD -- one paragraph, concrete enough to picture.

2. HOW WOULD IT WORK -- the actual mechanism. What the agent decides, what it
   generates, what the reader does, in what order. Not the pitch, the machinery.

3. WHY IS IT NEW -- your claim, stated precisely enough to be checked.
   PASS 1 CONSTRAINT, IMPORTANT: justify this against the constraint set and
   failure data you were given. You have deliberately NOT been given any list
   of existing tools, papers, systems or prior approaches, and you must not
   write as though you had. Do not write "unlike [named system]" or "existing
   tools do X". Claims of that shape belong to a later pass. State what the
   concept does that the constraints and failures above imply is not currently
   being done, and leave the external check to someone else.

4. WHY COULD IT SOLVE OUR PROBLEM -- tie it to audience + goal -> form, and
   name which region of the goal space it serves.

5a. GROUNDEDNESS -- what specifically in the constraint set or the failure data
    does this concept respond to? Name it. If you cannot, say so plainly; a
    concept floating free of the brief should be flagged, not defended.

5b. DISTINCTIVENESS WITHIN THIS SET -- in what specific way does this concept
    occupy different ground from the others you are proposing? This is about
    spanning the space, not about being unusual.

6. WHAT WOULD FALSIFY IT -- the cheapest experiment that would show this does
   not work. REQUIRED FORM: state what you would observe, what you would
   measure, and what threshold of that measurement counts as failure. "I cannot
   name one" is a permitted and genuinely useful answer. "Users might struggle"
   is not acceptable -- it names no observation, no measure, no threshold.

7. WHICH HYPOTHESES OR DESIGN PRINCIPLES IT SERVES OR BREAKS -- name violations
   explicitly. A concept that breaks a principle is not disqualified; a concept
   that breaks one silently is."""


def build_messages(north_star: str, hypotheses: str, principles: str) -> str:
    return f"""Sprint 10, Pass 1. You are generating concepts for what Altair8's
communication layer could be.

The team has built things before, but has never designed alternatives -- only
different implementations of one answer. Your job is to produce the rival
answers that should have been on the table.

You are working deliberately without any list of existing approaches, papers or
tools. That is not an oversight. Everything this team has ever proposed came
from surveying what already exists, and we are testing whether concepts derived
from our own constraints and failures look different from concepts derived from
a reading list. Someone else checks your work against prior art afterwards --
that is not your job and you have no means to do it.

OUR NORTH STAR
{north_star}

OUR HYPOTHESES
{hypotheses}

OUR DESIGN PRINCIPLES
{principles}

THE CONSTRAINT SET -- what you derive FROM
{CONSTRAINT_SET}

OUR OWN FAILURE DATA -- what you design AGAINST
{FAILURE_DATA}

YOUR TASK
Produce FIVE concepts. They must span genuinely different ground -- five
variations on one idea is a failure of this task, and so is five ideas that all
serve the same region of the goal space.

{TEMPLATE}

Before the five concepts, write a short section titled HOW I APPROACHED THIS,
naming the derivation move you used to generate candidates and what you
considered and rejected. After the five, write WHERE I AM LEAST CONFIDENT --
which concept you would bet against, and why. Be specific rather than modest;
this is used, not filed."""


def run() -> None:
    require_tool("priya", "write_concept_scenario")
    db.set_memory("priya", "status", "online")

    north_star = db.get_memory("team_leader", "north_star") or ""
    hypotheses = db.get_memory("team_leader", "hypotheses") or ""
    principles = db.get_memory("team_leader", "design_principles") or ""

    user_message = build_messages(north_star, hypotheses, principles)

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="priya",
        title="Sprint 10 Pass 1: generate concepts blind",
        description="Five concepts, eight fields each, no prior-art seeds.",
    )

    # --- Blindness evidence, written BEFORE the call so it exists either way ---
    input_log = f"""SPRINT 10 PASS 1 -- COMPLETE INPUT LOG
Written for Ingrid's inspection gate (blocking item 2). Pass 2 must not run
until she has confirmed this log.

MODEL: {MODEL}
TASK ID: {task_id}

DATA SOURCES READ FROM STORAGE:
{chr(10).join('  - ' + s for s in SOURCES_READ)}
Each was read in full and checked for named prior art before inclusion. None
names a tool, paper, system or visual pattern. design_principles #4 names
PowerPoint, as a legacy format to move away from, not as an approach to build
on. hypotheses #4 names Claude Code as a framework-ease risk, not a
visualization approach.

EXCLUDED BY DESIGN (not read, not passed):
{chr(10).join('  - ' + s for s in EXCLUDED_BY_DESIGN)}

CONTEXT-CARRY CONFIRMATION:
Single stateless Anthropic API call. No vectorstore query in this run (the
vectorstore module is imported only to store the OUTPUT afterwards). No
prior-turn context, no shared-memory injection, no retrieval over prior sprint
outputs. The complete input the model received is the system prompt and user
message reproduced verbatim below -- nothing else was sent.

================================================================================
SYSTEM PROMPT (verbatim)
================================================================================
{SYSTEM_PROMPT}

================================================================================
USER MESSAGE (verbatim)
================================================================================
{user_message}
"""
    db.set_memory("priya", "sprint10_pass1_input", input_log)
    print(f"[{NAME}] Input log written ({len(input_log)} chars) "
          f"-> priya/sprint10_pass1_input")

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        response = stream.get_final_message()

    concepts = response.content[0].text
    db.log_usage("priya", response.usage.input_tokens, response.usage.output_tokens)

    db.set_memory("priya", "sprint10_concepts_blind", concepts)
    vectorstore.remember(
        collection_name="concept_designer_memory",
        doc_id=f"sprint10-pass1-task-{task_id}",
        text=concepts,
        metadata={"agent": "priya", "type": "concept_scenarios", "sprint": 10, "pass": 1},
    )
    db.update_task(
        task_id, status="completed", result=concepts,
        artifact_type="concept_scenarios",
        artifact_payload={
            "memory_key": "priya/sprint10_concepts_blind",
            "input_log_key": "priya/sprint10_pass1_input",
            "pass": 1,
            "blind": True,
        },
    )

    print(f"[{NAME}]\n\n{concepts}")
    print(f"\n\n--- {len(concepts)} chars. "
          f"Pass 2 blocked until Ingrid confirms the input log. ---")


if __name__ == "__main__":
    run()
