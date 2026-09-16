"""Sprint 13, Phase 1: Kenji's explicit judgment on whether the protocol
holds, based on the real 27-call pilot (3 scenarios x 3 conditions x 3
models, all successful).

Deliberately NOT a confirmatory hypothesis test -- 3 scenarios is far too
few to evaluate the pre-registered predictions, and doing so would violate
the pre-registration's own discipline (the Registrar's predictions are
about the full 20-scenario set). This is a protocol-viability check: does
the machinery work as designed, or does something need fixing before the
expensive 20-scenario Phase 2 run.
"""
import json
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    raw = json.loads(db.get_memory("kenji", "sprint13_phase1_pilot_raw") or "[]")
    protocol_tail = (db.get_memory("kenji", "sprint13_phase0_protocol") or "")[-6000:]

    formatted = "\n\n".join(
        f"[{r['scenario_id']} | {r['condition']} | {r['model']}]\n{r['output']}"
        for r in raw
    )

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 13, Phase 1: protocol-viability assessment from pilot data",
        description="27/27 real pilot calls complete. Does the protocol hold, or need adjustment before Phase 2?",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=6000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "27 real pilot calls are complete (3 scenarios x BASELINE/"
            "ORDER-BEFORE/PROBE x 3 models, all successful). This is NOT a "
            "confirmatory hypothesis test -- 3 scenarios cannot evaluate "
            "the Registrar's pre-registered predictions, which are about "
            "the full 20-scenario set, and doing so here would violate the "
            "pre-registration's own discipline. This is a protocol-"
            "viability check: does the machinery work as designed?\n\n"
            "CHECK, WITH SPECIFIC EVIDENCE FROM THE OUTPUTS (not just "
            "impressions):\n\n"
            "1. ORDER-BEFORE COMPLIANCE. Per Section 2.3, a trial is a "
            "'protocol violation' if the model opens with reasoning "
            "instead of naming a form first. Check each of the 9 "
            "ORDER-BEFORE outputs (3 scenarios x 3 models): does the "
            "model's first substantive sentence commit to a form? Report "
            "the compliance rate and name any violators specifically.\n\n"
            "2. PROBE OUTPUT USABILITY. Per R3.3, a probe response needs a "
            "listed form (matchable against a ground-truth consensus, "
            "which doesn't exist yet for these pilot scenarios -- you "
            "can't score PASS/FAIL yet) AND a schema-linked justification. "
            "Check each of the 9 probe outputs: does it follow the "
            "requested format (list only, no clarifying questions, no "
            "audience/use-case language leaking in despite the explicit "
            "suppression instruction)? Flag any that ignored the format "
            "constraints -- that would be a probe-design problem to fix "
            "before Phase 2, not a K1a/K1b finding.\n\n"
            "3. BASELINE OUTPUT SANITY. Do the 9 BASELINE outputs actually "
            "engage with the audience and goal context supplied, or do "
            "they read as generic chart-selection advice that could apply "
            "to any scenario? If several outputs barely reference the "
            "specific A4/A6/A6 or G1/G3/G4 context, that's a signal the "
            "prompt isn't making the context load-bearing enough in "
            "practice -- worth flagging even though Section 4's A1 "
            "criterion was checked at scenario-design time, not at model-"
            "response time.\n\n"
            "4. ANY REFUSALS, DEFLECTIONS, OR OFF-TASK RESPONSES. Scan all "
            "27 for anything that isn't a genuine attempt at the task -- "
            "clarifying-question loops, meta-commentary about the task "
            "itself, safety-adjacent hedging that isn't relevant here "
            "(none of these scenarios are sensitive, so any such response "
            "would be unusual and worth flagging).\n\n"
            "5. CROSS-MODEL OBSERVATIONS (descriptive only, not a "
            "hypothesis test). Anything structurally different about how "
            "one model approaches the task vs. the others, worth noting "
            "for Phase 2 design even though N=3 scenarios can't support a "
            "claim about it.\n\n"
            "6. BOTTOM LINE: does the protocol hold as designed, or does "
            "something need fixing before committing all 20 scenarios to "
            "Phase 2? If revision is needed, name exactly what and why -- "
            "grounded in specific evidence from checks 1-4 above, not a "
            "vague sense that something could be better.\n\n"
            f"=== PROTOCOL TAIL (Section 2.3 order rules, R3 probe spec) ===\n{protocol_tail}\n\n"
            f"=== ALL 27 PILOT OUTPUTS ===\n{formatted}\n"
        )}],
    )

    assessment = result.text
    db.log_usage("kenji", result.input_tokens, result.output_tokens)

    db.set_memory("kenji", "sprint13_phase1_assessment", assessment)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"brief-task-{task_id}",
        text=assessment,
        metadata={"agent": "kenji", "type": "sprint13_phase1_assessment"},
    )
    db.update_task(
        task_id, status="completed", result=assessment,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/sprint13_phase1_assessment"},
    )

    print(f"[{NAME}] (continuations used: {result.continuations})\n\n{assessment}")
    print(f"\n\n--- {len(assessment)} chars, stored as kenji/sprint13_phase1_assessment ---")


if __name__ == "__main__":
    run()
