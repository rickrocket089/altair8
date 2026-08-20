"""Sprint 11 gate 2: formally specify the minimum-spanning-argument scaffold.

Ingrid's condition 2 on the Sprint 10 close, and she called it a Sprint 11
blocker in plain terms: C1 uses the phrase "minimum-spanning-argument"
throughout as though it has a settled meaning, but computing the
minimum-confidence-spanning path through an argument map is a non-trivial
algorithmic question that was never defined at concept stage. Her words: "This
will bite Mateo in Sprint 11. It should have been defined at the concept stage."

Mateo specifies it because he will build it. He is given Priya's concept text
as the statement of intent -- he is not free to redefine what the scaffold is
FOR, only to determine what it concretely IS.

The output that matters most is not the algorithm. It is the list of decisions
the concept left underdetermined, because those are the points where an
implementer silently invents semantics the concept never authorised. That is
the same class of failure as Sprint 8's data-flow gap: a stage inventing
specifics because nobody passed it the real ones.
"""
import os
import re

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.developer.persona import NAME, SYSTEM_PROMPT
from agents.permissions import require_tool
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"


def run() -> None:
    require_tool("mateo", "read_brief")
    db.set_memory("mateo", "status", "online")

    concepts = db.get_memory("priya", "sprint10_concepts_blind") or ""
    m = re.search(r"#\s*CONCEPT 1:.*?(?=^#\s*CONCEPT 2:)", concepts, re.S | re.M)
    c1 = m.group(0) if m else concepts[:8000]

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="mateo",
        title="Sprint 11 gate 2: specify the minimum-spanning-argument scaffold",
        description="Ingrid condition 2, blocking. Must be settled before the C1 build starts.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model=MODEL, max_tokens=10000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "The founder has chosen C1 (The Commitment Audit) as Altair8's "
            "direction. You will build it. Before you do, one thing has to be "
            "settled.\n\n"
            "The reviewer blocked the build on this: C1 uses the phrase "
            "'minimum-spanning-argument' as though it has a settled meaning. "
            "It does not. Computing the minimum-confidence-spanning path "
            "through an argument map is a non-trivial algorithmic question "
            "that was never defined when the concept was written. Her warning "
            "was specific -- this will bite you during the build.\n\n"
            "Specify it now.\n\n"
            "Your constraint: the concept text below is the statement of "
            "INTENT. You determine what the scaffold concretely IS. You do not "
            "get to redefine what it is FOR. Where the concept's intent is "
            "genuinely ambiguous, do not resolve it silently -- surface it "
            "(see section 4).\n\n"
            f"C1 AS SPECIFIED BY ITS DESIGNER:\n{c1}\n\n"
            "PRODUCE:\n\n"
            "1. THE DATA STRUCTURE. What exactly is the argument map? Nodes "
            "are claims with an epistemic category and a confidence score; "
            "edges are dependencies. Is it a DAG? Can it cycle? Can it be "
            "disconnected? Must every claim reach the main claim? State what "
            "the structure guarantees, because the algorithm depends on it.\n\n"
            "2. THE ALGORITHM. Define the minimum-spanning-argument path "
            "precisely: inputs, output, and the actual selection rule. Note "
            "that 'minimum spanning' is borrowed from graph theory where it "
            "means something specific (minimum spanning TREE, over edge "
            "weights) and that is probably NOT what this needs -- the concept "
            "wants the fewest nodes that establish the main claim at highest "
            "confidence, which is closer to a constrained subgraph selection "
            "or a shortest-path-with-node-weights problem. Say what it "
            "actually is. If the borrowed name is misleading, say so and "
            "propose a better one.\n\n"
            "3. EDGE CASES, each with the behaviour you propose: no claim "
            "above threshold; several equally minimal paths; a low-confidence "
            "claim that is structurally unavoidable; an assumption that "
            "everything depends on; a main claim resting only on assertions.\n\n"
            "4. WHAT THE CONCEPT LEFT UNDERDETERMINED -- the most important "
            "section. List every decision you had to make that the concept "
            "does not actually specify, and for each, say what you chose and "
            "what a different choice would have produced. These are the points "
            "where an implementer silently invents semantics nobody "
            "authorised, and this project already has one documented case of "
            "exactly that: a pipeline stage that invented specifics because "
            "nobody passed it the real ones. Do not smooth these over.\n\n"
            "5. COMPLEXITY AND BUILD COST: is this buildable in one sprint "
            "alongside the rest of the C1 prototype? Answer honestly -- if the "
            "algorithm is the expensive part, that changes what the sprint can "
            "contain.\n\n"
            "6. WHAT YOU WOULD NEED FROM THE CONCEPT'S DESIGNER before "
            "building, if anything. A question asked now is cheaper than a "
            "wrong assumption discovered later."
        )}],
    ) as stream:
        response = stream.get_final_message()

    spec = response.content[0].text
    db.log_usage("mateo", response.usage.input_tokens, response.usage.output_tokens)

    db.set_memory("mateo", "c1_spanning_scaffold_spec", spec)
    vectorstore.remember(
        collection_name="developer_memory",
        doc_id=f"c1-scaffold-task-{task_id}", text=spec,
        metadata={"agent": "mateo", "type": "algorithm_spec", "sprint": 11, "concept": "C1"},
    )
    db.update_task(
        task_id, status="completed", result=spec,
        artifact_type="algorithm_spec",
        artifact_payload={"memory_key": "mateo/c1_spanning_scaffold_spec"},
    )

    print(f"[{NAME}]\n\n{spec}")


if __name__ == "__main__":
    run()
