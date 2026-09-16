"""Sprint 14, Phase 0 gate -- Ingrid reviews Kenji's audience-optimal
protocol before the Registrar starts ranking, and before Draco generates
any candidate sets.

Four things surfaced by Kenji as needing Sophie's call: the NOT-IN-SET
scoring rule, threshold-edge-case handling, Registrar identity, and
confirming the formal pre-registration is a separate deliverable. Ingrid
addresses what she can (methodology) and flags what's genuinely Sophie's.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")

    protocol = db.get_memory("kenji", "sprint14_phase0_protocol") or ""
    option3_check = db.get_memory("kenji", "sprint14_option3_check") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Sprint 14 Phase 0 gate: audience-optimal protocol review",
        description="Registrar cannot start ranking, Draco cannot generate candidate sets, until this gate passes.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=6000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Gate review of Kenji's Sprint 14 Phase 0 protocol -- the "
            "form-valid-but-suboptimal (FVBS) criterion, before the "
            "Registrar ranks anything or Draco generates candidate sets.\n\n"
            "CHECK, IN ORDER:\n\n"
            "1. THE TOP-1 THRESHOLD. Kenji argues top-1 (not top-2) because "
            "a looser threshold would let convention-reproduction pass by "
            "chance. Verify the math: with 4 candidates and a top-1 "
            "threshold, is 25% really the right random baseline, or does "
            "it depend on assumptions about the distribution of Draco's "
            "candidate quality that aren't stated? Is top-1 too strict in "
            "the other direction -- could it produce false FVBS "
            "classifications when rank-1 and rank-2 are genuinely close "
            "calls, inflating the failure rate for reasons unrelated to "
            "audience reasoning?\n\n"
            "2. THE CIRCULARITY FIX, VERIFIED END TO END. Walk through the "
            "actual sequence (Draco generates candidates -> Ingrid spot-"
            "checks -> Registrar ranks blind to outputs -> Ingrid locks via "
            "hash -> only then Phase 1 starts) and confirm it actually "
            "closes the self-grading loop Kenji's own Option 3 check "
            "identified. Is there any remaining path by which the ranking "
            "could be influenced by knowledge of model behavior -- for "
            "instance, does Draco's own candidate-generation process carry "
            "any information from Sprint 13, or is it purely a function of "
            "the (unchanged) scenario schemas?\n\n"
            "3. THE TWO-FAILURE-TYPE RECORDING (Section 2). Verify the "
            "four-outcome table and the N_TOTAL integrity check are "
            "actually sufficient to prevent one failure type masking the "
            "other -- is there a scenario this table doesn't handle "
            "cleanly (e.g. the NOT-IN-SET case Kenji flagged in Section 5, "
            "which doesn't fit neatly into the four rows)?\n\n"
            "4. THE FOUR ROLE-BOUNDARY FLAGS. For each, either resolve it "
            "yourself if it's genuinely a methodology question, or confirm "
            "it truly requires Sophie: (a) NOT-IN-SET scoring rule, (b) "
            "threshold edge-case handling, (c) Registrar identity -- this "
            "one is clearly Sophie's, just confirm -- (d) pre-registration "
            "as a separate deliverable.\n\n"
            "5. THE PREDICTION (Section 7, 35-55% FVBS rate). Sanity-check "
            "the reasoning -- does the argument that novel-context/extreme "
            "cells are where convention and audience-optimal form diverge "
            "most actually support this specific range, or is 35-55% an "
            "arbitrary band around a plausible-sounding midpoint? Also "
            "confirm Kenji's own instruction to himself (not to let "
            "memory of Sprint 13 outputs leak into this reasoning) was "
            "actually followed -- does anything in Section 7 read as if it "
            "were informed by remembered specific model behavior rather "
            "than the structural argument alone?\n\n"
            "6. GATE VERDICT: PROCEED (Registrar can start ranking, Draco "
            "can generate candidate sets), REVISE (name exactly what), or "
            "BLOCKED.\n\n"
            f"=== KENJI'S PHASE 0 PROTOCOL (FULL) ===\n{protocol}\n\n"
            f"=== OPTION 3 CIRCULARITY CHECK, FOR CONTEXT ===\n{option3_check[:4000]}\n"
        )}],
    )

    gate = result.text
    db.log_usage("ingrid", result.input_tokens, result.output_tokens)

    db.set_memory("ingrid", "sprint14_phase0_gate", gate)
    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"review-task-{task_id}",
        text=gate,
        metadata={"agent": "ingrid", "type": "sprint14_phase0_gate"},
    )
    db.update_task(
        task_id, status="completed", result=gate,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/sprint14_phase0_gate"},
    )

    print(f"[{NAME}] (continuations: {result.continuations})\n\n{gate}")
    print(f"\n\n--- {len(gate)} chars, stored as ingrid/sprint14_phase0_gate ---")


if __name__ == "__main__":
    run()
