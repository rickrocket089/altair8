"""Sprint 10, Pass 2: Priya sighted.

Runs only after Ingrid's gate confirmed Pass 1 was genuinely blind
(ingrid/sprint10_pass1_blindness_gate: "PASS 1 CONFIRMED BLIND").

She now sees what was withheld -- the real candidate_approaches rows and
Naledi's Sprint 9 survey of novel visual primitives -- and answers a narrow
question: what do these add to, and what do they challenge in, what you
already wrote? Every change is attributed to the specific seed that caused it,
because the attribution IS the experiment. Pass 1 vs Pass 2 measures the pull
of explicit seeding.

Pass 1 is not modified. It stays at priya/sprint10_concepts_blind as the
preserved baseline; this writes a separate key.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.concept_designer.persona import NAME, SYSTEM_PROMPT
from agents.permissions import require_tool
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"


def run() -> None:
    require_tool("priya", "write_concept_scenario")
    db.set_memory("priya", "status", "online")

    gate = db.get_memory("ingrid", "sprint10_pass1_blindness_gate") or ""
    if "CONFIRMED BLIND" not in gate:
        raise SystemExit(
            "Pass 2 is gated: Ingrid has not confirmed Pass 1 was run blind. "
            "Run agents.reviewer.verify_pass1_blindness first."
        )

    blind = db.get_memory("priya", "sprint10_concepts_blind") or "(missing)"
    survey = db.get_memory("naledi", "novel_visual_primitives_survey") or "(missing)"

    rows = db.list_candidate_approaches()
    seeds = "\n\n".join(
        f"--- SEED {r.get('id')} [{r.get('category')}] {r.get('title')}\n"
        f"{r.get('description')}"
        for r in rows
    ) or "(none)"

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="priya",
        title="Sprint 10 Pass 2: sighted review of concepts against the seeds",
        description="What the withheld prior art adds to or challenges in Pass 1.",
    )

    user_message = f"""Sprint 10, Pass 2.

In Pass 1 you generated five concepts without any list of existing approaches.
That was deliberate, and it is now finished and preserved -- you are not being
asked to rewrite it, and it will be compared against what you do here.

You are now shown what was withheld. Your question is narrow: WHAT DO THESE ADD
TO, AND WHAT DO THEY CHALLENGE IN, WHAT YOU ALREADY WROTE?

================ YOUR PASS 1 OUTPUT ================
{blind}

================ WITHHELD MATERIAL 1: THE TEAM'S CANDIDATE APPROACHES ================
These are research leads the team flagged across earlier sprints -- papers,
patterns and tools someone thought worth revisiting. This is the reading list
you did not have.

{seeds}

================ WITHHELD MATERIAL 2: SPRINT 9'S SURVEY OF NOVEL VISUAL PRIMITIVES ================
A colleague surveyed data journalism, motion graphics, spatial interfaces, game
UI and scientific visualization for patterns with real generative ambition that
were never applied to business communication. Four were built as working
prototypes.

{survey}

================ YOUR TASK ================

Write four sections.

SECTION A -- WHAT THESE ADD.
For each of your five concepts, state whether the withheld material changes it,
and how. Attribute every change to the specific seed or pattern that caused it,
by name. "Concept 3 changes because of X" -- not "on reflection, concept 3
should change." The attribution is the point: we are measuring how far this
material pulls your thinking, so an unattributed change is a lost measurement.
If a concept is unchanged, say so plainly. Unchanged is a real and useful
answer, not a failure to engage.

SECTION B -- WHAT THESE CHALLENGE.
Where does the withheld material undercut, duplicate or weaken something you
proposed? Be specific about which of your claims no longer holds. If one of
your concepts turns out to be substantially the same idea as something in the
withheld material, say so directly -- that is exactly what this pass exists to
surface, and concealing it would corrupt the comparison. Note: someone else
still performs the formal prior-art check. You are reporting what you now see,
not delivering a verdict on originality.

SECTION C -- ADDITIONS, REVISIONS, WITHDRAWALS.
You may add new concepts, revise existing ones, or withdraw them. Any NEW
concept gets the full eight fields, same template as Pass 1, and must name
which seed prompted it. Any REVISION states what changed and why. Any
WITHDRAWAL states which seed made you withdraw it. If you make none of these
changes, say so and explain why the material did not warrant any.

SECTION D -- YOUR OWN READING OF THE DIFFERENCE.
Having now seen both, characterise the difference between what you produced
blind and what you would have produced sighted. Was the withheld material
generative for you, or did it mostly redescribe ground you had already covered?
Be honest in either direction. A finding that the reading list added little is
as valuable to this team as a finding that it added a lot -- and it is the more
uncomfortable one to report, so report it if it is true."""

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        response = stream.get_final_message()

    sighted = response.content[0].text
    db.log_usage("priya", response.usage.input_tokens, response.usage.output_tokens)

    db.set_memory("priya", "sprint10_concepts_sighted", sighted)
    vectorstore.remember(
        collection_name="concept_designer_memory",
        doc_id=f"sprint10-pass2-task-{task_id}",
        text=sighted,
        metadata={"agent": "priya", "type": "concept_scenarios", "sprint": 10, "pass": 2},
    )
    db.update_task(
        task_id, status="completed", result=sighted,
        artifact_type="concept_scenarios",
        artifact_payload={"memory_key": "priya/sprint10_concepts_sighted", "pass": 2, "blind": False},
    )

    print(f"[{NAME}]\n\n{sighted}")
    print(f"\n\n--- {len(sighted)} chars ---")


if __name__ == "__main__":
    run()
