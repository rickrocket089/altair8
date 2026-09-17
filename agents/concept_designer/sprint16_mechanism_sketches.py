"""Sprint 16, Question 1: Priya sketches 2-3 concrete mechanisms for how
the reconceived knowledge layer (compositional principle kept, primitive
vocabulary derived from browser/generative capability rather than
inherited from Draco) could actually improve form/artifact selection --
and names which one is the real bet.

Runs first in Sophie's Phase 0 -> Q1 -> Q2/Q3 -> Q4 -> Q5 sequence:
without a value-add claim, the prior-art check (Q2) and scaling question
(Q3) have nothing to evaluate against.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.concept_designer.persona import NAME, SYSTEM_PROMPT
from agents.permissions import require_tool
from tools import db, vectorstore
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"


def run() -> None:
    require_tool("priya", "write_concept_scenario")
    db.set_memory("priya", "status", "online")

    phase0_brief = db.get_memory("team_leader", "sprint16_phase0_brief") or ""
    original_fge = db.get_memory("priya", "sprint15_concepts") or ""
    fge_start = original_fge.find("## CONCEPT 2")
    fge_end = original_fge.find("## CONCEPT 3")
    original_fge_excerpt = original_fge[fge_start:fge_end] if fge_start != -1 else original_fge[:4000]

    reality_check = db.get_memory("kenji", "sprint15_reality_check") or ""
    ingrid_review = db.get_memory("ingrid", "sprint15_concepts_review") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="priya",
        title="Sprint 16, Q1: mechanism sketches for the reconceived knowledge layer",
        description="2-3 concrete mechanisms, value-add as a testable claim, name the real bet.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=8000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Sprint 16, Question 1 of 5. Your own Concept 2 (FGE, Form "
            "Grammar Extension) from Sprint 15 was the team's top-ranked "
            "concept, but the founder correctly pushed back on its "
            "premise: it inherited its primitive vocabulary from Draco "
            "(a statistical-chart grammar), which structurally "
            "contradicts Design Principle #4 and the North Star's "
            "browser-substrate position. Read the phase 0 brief below "
            "for the full reframe.\n\n"
            "TASK: sketch 2-3 concrete MECHANISMS for how a knowledge "
            "layer of this reconceived kind could actually work -- not "
            "8-field concept write-ups like Sprint 15, but mechanism "
            "sketches focused specifically on: what does the system DO "
            "differently at generation time because this knowledge layer "
            "exists, and why would that reduce Sprint 14's measured "
            "failures (FVBS 53.9%, NOT-IN-SET 26.7%, now understood as "
            "including a real vocabulary ceiling AND a Draco-cost-"
            "ranking-exclusion artifact)?\n\n"
            "For each mechanism sketch, cover:\n"
            "1. THE MECHANISM -- what changes at generation time, "
            "concretely, because of this knowledge layer.\n"
            "2. VALUE-ADD AS A TESTABLE CLAIM -- not 'this should help' "
            "but a specific, falsifiable statement of what would improve "
            "and how you'd know.\n"
            "3. WHY BROWSER-NATIVE, NOT CHART-NATIVE -- does this "
            "mechanism genuinely extend past chart-shaped output "
            "(illustration, motion, interaction, diegetic embedding, "
            "generated imagery), or does it just relabel the same chart-"
            "taxonomy idea? Be self-critical here -- it is very easy to "
            "redraw the same box with a new label.\n"
            "4. WHAT IT DOES NOT SOLVE -- name the failure mode this "
            "mechanism has no answer for.\n\n"
            "After the 2-3 sketches, state plainly which one is THE REAL "
            "BET -- the one you'd actually build first, and why the "
            "others are not that. This recommendation drives the rest of "
            "Sprint 16 (the prior-art check, scaling sketch, and "
            "transition plan all evaluate against whichever mechanism "
            "you name here), so do not hedge it into mush -- if you "
            "genuinely can't choose, say so and say what would resolve "
            "it.\n\n"
            f"=== SPRINT 16 PHASE 0 BRIEF (the reframe, in full) ===\n{phase0_brief}\n\n"
            f"=== YOUR OWN SPRINT 15 FGE CONCEPT (for reference -- you are "
            f"revising its mechanism, not repeating its Draco-bound "
            f"vocabulary) ===\n{original_fge_excerpt}\n\n"
            f"=== KENJI'S REALITY CHECK ON FGE (Sprint 15) ===\n"
            f"{reality_check[reality_check.find('CONCEPT 2'):reality_check.find('CONCEPT 3')] if 'CONCEPT 2' in reality_check else reality_check[:3000]}\n\n"
            f"=== INGRID'S REVIEW NOTES RELEVANT TO FGE ===\n"
            f"{ingrid_review[ingrid_review.find('FGE'):ingrid_review.find('FGE')+3000] if 'FGE' in ingrid_review else ''}\n"
        )}],
    )

    sketches = result.text
    db.log_usage("priya", result.input_tokens, result.output_tokens)

    db.set_memory("priya", "sprint16_mechanism_sketches", sketches)
    vectorstore.remember(
        collection_name="concept_designer_memory",
        doc_id=f"sprint16-mechanism-sketches-task-{task_id}",
        text=sketches,
        metadata={"agent": "priya", "type": "sprint16_mechanism_sketches"},
    )
    db.update_task(
        task_id, status="completed", result=sketches,
        artifact_type="concept_scenarios",
        artifact_payload={"memory_key": "priya/sprint16_mechanism_sketches"},
    )

    print(f"[{NAME}] (continuations: {result.continuations})\n\n{sketches}")
    print(f"\n\n--- {len(sketches)} chars, stored as priya/sprint16_mechanism_sketches ---")


if __name__ == "__main__":
    run()
