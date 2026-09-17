"""Sprint 16, Question 4: Mateo's technical-feasibility consult on 1-2
transition plans toward a Sprint 17 prototype of Mechanism A
(Compositional Rendering Contracts). Consult only -- no code, no
prototype file, per Sprint 16's explicit no-build scope.

Informed by the Knowledge Systems Architect's scaling sketch, which
identified slot checkability (a capability slot must be a verifiable
claim against a declared rendering environment, not just a label) as the
architecture's single load-bearing property -- and named it as the thing
most likely to degrade silently under pressure to demonstrate vocabulary
breadth. Mateo's job is to assess whether that property is actually
buildable, and if so, what the minimal proof looks like.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.developer.persona import NAME, SYSTEM_PROMPT
from agents.permissions import require_tool
from tools import db, vectorstore
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"


def run() -> None:
    require_tool("mateo", "write_task_artifact")
    db.set_memory("mateo", "status", "online")

    mechanism_sketches = db.get_memory("priya", "sprint16_mechanism_sketches") or ""
    mech_a_start = mechanism_sketches.find("## Mechanism Sketch A")
    mech_a_end = mechanism_sketches.find("## Mechanism Sketch B")
    mechanism_a = mechanism_sketches[mech_a_start:mech_a_end] if mech_a_start != -1 else mechanism_sketches[:5000]

    priorart_check = db.get_memory("kenji", "sprint16_priorart_check") or ""
    seed_contracts = priorart_check[priorart_check.find("CHECK 4"):priorart_check.find("## SUMMARY TABLE")]

    scaling_sketch = db.get_memory("knowledge_architect", "sprint16_scaling_sketch") or ""
    handoff = scaling_sketch[scaling_sketch.find("## Handoff Summary"):]
    slot_discipline = scaling_sketch[scaling_sketch.find("## Level 2"):scaling_sketch.find("## Level 3")]

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="mateo",
        title="Sprint 16, Q4: technical-feasibility consult on Sprint 17 transition plans",
        description="Consult only -- no code, no prototype file. Estimate feasibility, propose 1-2 transition plans.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=6000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Sprint 16, Question 4 of 5: technical-feasibility consult, "
            "not a build. Sprint 16 is explicitly concepts-only -- do "
            "not write a prototype or code, propose what a Sprint 17 "
            "prototype COULD concretely be and how hard it would "
            "actually be to build.\n\n"
            "Mechanism A (Compositional Rendering Contracts) stores "
            "visual forms as capability-contracts: declared capability "
            "slots + a composition rule, checked against what a "
            "rendering environment can actually execute, with a partial-"
            "satisfaction score when the environment can't fully satisfy "
            "a contract. The Knowledge Systems Architect's scaling "
            "sketch (below) identified SLOT CHECKABILITY -- a capability "
            "slot must be a verifiable claim against a declared "
            "rendering environment, not just a descriptive label -- as "
            "the architecture's single load-bearing property, and warned "
            "it is exactly the thing likely to degrade silently under "
            "pressure to show vocabulary breadth quickly.\n\n"
            "We already have 6 concrete seed contracts to work from: the "
            "5 Sprint 14 NOT-IN-SET statistical forms (violin, raincloud, "
            "beeswarm, dumbbell, KDE density) plus 3 confirmed non-chart "
            "contracts (Slider, Carousel, Annotated Pyramid), each fully "
            "specified with capability slots and composition rules.\n\n"
            "YOUR TASK:\n\n"
            "1. PROPOSE 1-2 CONCRETE TRANSITION PLANS for a Sprint 17 "
            "prototype. For each: what's the smallest thing that would "
            "actually test whether slot checkability works in practice "
            "-- i.e. can you declare a rendering environment's real "
            "capabilities (what your current frontend stack can actually "
            "execute) and check a handful of contracts against it, "
            "getting real partial-satisfaction scores, not simulated "
            "ones? Consider at minimum: (a) a minimal 'rendering "
            "environment declaration + contract checker' that proves "
            "checkability end to end on the 6 seed contracts, without "
            "any ranking/ crawl/knowledge-base machinery at all; (b) "
            "whatever second option you think is genuinely worth naming "
            "as an alternative -- don't force a second option if the "
            "first is clearly right, say so instead.\n\n"
            "2. TECHNICAL REALISM. For your top plan: which subsystem "
            "gets built first, what are the real data structures (be "
            "concrete -- what does a contract record actually look like "
            "as data, what does a rendering-environment declaration look "
            "like), what interfaces are needed between them. Name what "
            "you're NOT sure is buildable yet and why (e.g. can you "
            "actually declare 'this environment satisfies force-layout-"
            "simulation' in a way that's checkable, or is that itself "
            "still fuzzy?).\n\n"
            "3. HONEST DIFFICULTY ASSESSMENT. Of the 6 seed contracts, "
            "which is the easiest to prove checkability on first (best "
            "first target), and which is hardest / most likely to reveal "
            "that the 'checkability' claim doesn't actually hold up in "
            "practice? Say plainly if you think the checkability property "
            "itself might not survive contact with a real implementation "
            "-- that would be an important finding, not something to "
            "soften.\n\n"
            f"=== MECHANISM A (Priya's sketch) ===\n{mechanism_a}\n\n"
            f"=== THE 6 SEED CONTRACTS (from Kenji's Check 4) ===\n{seed_contracts}\n\n"
            f"=== SLOT CHECKABILITY DISCIPLINE (Knowledge Architect, Level 2) ===\n{slot_discipline}\n\n"
            f"=== SCALING SKETCH HANDOFF SUMMARY ===\n{handoff}\n"
        )}],
    )

    consult = result.text
    db.log_usage("mateo", result.input_tokens, result.output_tokens)

    db.set_memory("mateo", "sprint16_transition_consult", consult)
    vectorstore.remember(
        collection_name="developer_memory",
        doc_id=f"sprint16-transition-consult-task-{task_id}",
        text=consult,
        metadata={"agent": "mateo", "type": "sprint16_transition_consult"},
    )
    db.update_task(
        task_id, status="completed", result=consult,
        artifact_type="brief",
        artifact_payload={"memory_key": "mateo/sprint16_transition_consult"},
    )

    print(f"[{NAME}] (continuations: {result.continuations})\n\n{consult}")
    print(f"\n\n--- {len(consult)} chars, stored as mateo/sprint16_transition_consult ---")


if __name__ == "__main__":
    run()
