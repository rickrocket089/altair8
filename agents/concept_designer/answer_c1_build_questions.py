"""Sprint 11: Priya answers the five questions blocking the C1 build.

Mateo specified the primary reading path (formerly "minimum-spanning-argument"
-- he found the graph-theory borrowing misleading) and surfaced two things the
concept could not settle on its own: seven decisions it left underdetermined,
where he had to choose and said so; and five questions where a wrong assumption
produces a different system.

Priya answers because they are questions of intent and C1 is her concept.

She is asked to do two jobs, not one:
  - answer Q1-Q5 with decisions Mateo can build against;
  - review the seven defaults he chose in her absence and either endorse or
    override each. Those are the points where an implementer invents semantics
    nobody authorised. This project has one documented instance of exactly that
    (Sprint 8: a pipeline stage inventing specifics because nobody passed it the
    real ones), which is the failure C1 exists to address.

She is explicitly permitted to answer "this is the founder's call" or "I do not
know" -- a fabricated decision is worse than a named gap, and she has no
authority over product direction.
"""
import os
import re

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

    concepts = db.get_memory("priya", "sprint10_concepts_blind") or ""
    m = re.search(r"#\s*CONCEPT 1:.*?(?=^#\s*CONCEPT 2:)", concepts, re.S | re.M)
    c1 = m.group(0) if m else concepts[:8000]

    spec = db.get_memory("mateo", "c1_spanning_scaffold_spec") or "(missing)"
    priorart = db.get_memory("kenji", "c1_argument_visualization_check") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="priya",
        title="Sprint 11: answer the five questions blocking the C1 build",
        description="Intent decisions Mateo cannot make. Build is blocked until these land.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model=MODEL, max_tokens=12000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "The founder chose C1 as Altair8's direction. Mateo has specified "
            "the reading-path algorithm and is ready to build. He is blocked on "
            "five questions only you can answer, and he made seven decisions in "
            "your absence that you should either endorse or overrule.\n\n"
            "Two notes before you answer.\n\n"
            "First: he found that 'minimum-spanning-argument' was a misleading "
            "borrowing from graph theory -- minimum spanning tree means "
            "something specific about edge weights, and that is not what your "
            "concept wants. He renamed it the primary reading path. If you "
            "disagree with the rename, say so; otherwise adopt it, because the "
            "old name was importing a guarantee the algorithm does not "
            "provide.\n\n"
            "Second: Kenji's prior-art check on C1 has come back. It matters "
            "for your answers because it tells you which parts of this concept "
            "are load-bearing for its contribution and which are conventional. "
            "Do not defend a decision because it is yours; defend it because it "
            "does work the concept needs.\n\n"
            "YOU MAY DECLINE TO DECIDE. 'This is the founder's call' and 'I do "
            "not know, here is what would settle it' are both acceptable and "
            "useful answers. A fabricated decision that Mateo builds against is "
            "far worse than a named gap. You have no authority over product "
            "direction.\n\n"
            f"=== YOUR CONCEPT, C1 AS WRITTEN ===\n{c1}\n\n"
            f"=== MATEO'S SPECIFICATION, DEFAULTS AND QUESTIONS ===\n{spec}\n\n"
            f"=== KENJI'S PRIOR-ART CHECK ON C1 ===\n{priorart[:12000]}\n\n"
            "=== PRODUCE ===\n\n"
            "PART A -- ANSWER Q1 THROUGH Q5. For each: the decision, one "
            "paragraph of reasoning, and what it commits the build to. Be "
            "specific enough that Mateo can act without coming back.\n\n"
            "Q3 deserves more than the others. He asks whether the intended "
            "architecture re-introduces a stage boundary between the audit and "
            "the render. Stage separation causing confabulated content to pass "
            "structural checks is the failure your concept was written to "
            "address. If C1's own architecture recreates that boundary, the "
            "concept undermines itself, and you should say so plainly rather "
            "than route around it.\n\n"
            "PART B -- REVIEW HIS SEVEN DEFAULTS (his section 4). For each: "
            "ENDORSE or OVERRIDE, with a sentence of reasoning. If you "
            "override, state what he should do instead. Pay particular "
            "attention to his choice of stepped rather than continuous visual "
            "weight -- his argument is that continuous encoding implies a "
            "precision that ordinal confidence scores do not have. That "
            "argument bears directly on your central claim that visual weight "
            "encodes confidence rather than rhetorical emphasis, so decide it "
            "on the merits.\n\n"
            "PART C -- WHAT KENJI'S FINDINGS CHANGE, if anything. He found "
            "argument mapping is an established field, typed argumentative "
            "classification is existing work, and Explorable Theorems is a "
            "structural analogue for the layered default-path architecture. "
            "Does any of that change what C1 should be, as opposed to how it "
            "should be described? Be honest if the answer is that the "
            "contribution is thinner than it looked.\n\n"
            "PART D -- WHAT YOU ARE STILL WORRIED ABOUT. One short section. "
            "Not a summary."
        )}],
    ) as stream:
        response = stream.get_final_message()

    answers = response.content[0].text
    db.log_usage("priya", response.usage.input_tokens, response.usage.output_tokens)

    db.set_memory("priya", "c1_build_question_answers", answers)
    vectorstore.remember(
        collection_name="concept_designer_memory",
        doc_id=f"c1-answers-task-{task_id}", text=answers,
        metadata={"agent": "priya", "type": "build_decisions", "sprint": 11, "concept": "C1"},
    )
    db.update_task(
        task_id, status="completed", result=answers,
        artifact_type="build_decisions",
        artifact_payload={"memory_key": "priya/c1_build_question_answers"},
    )

    print(f"[{NAME}]\n\n{answers}")


if __name__ == "__main__":
    run()
