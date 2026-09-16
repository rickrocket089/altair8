"""Ingrid's output-verification spot-check on Draco's candidate sets,
per Sprint 14 Phase 0 protocol Section 3: before candidates go to the
Registrar, verify at least 4 of 20 scenario candidate sets actually pass
F1/F2/F3 for that scenario (Draco's cost-based selection is a structural-
constraint optimization, not an F1/F2/F3 check -- they're related but not
identical, and this is exactly the "completing without an exception is not
evidence of correctness" principle applied here).

Mechanical checks (no duplicates, randomization spread) were already done
directly in Python, not by an LLM -- this script covers only the content
judgment (does each candidate form actually pass F1/F2/F3 for its
scenario), which requires real reasoning about the scenario semantics.
"""
import json
import os
import random

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"

AUDIENCE = {
    "A1": "familiar with the measurement domain, unfamiliar with this specific dataset",
    "A2": "no domain vocabulary, accustomed to everyday quantitative comparisons",
    "A3": "monitors this metric repeatedly, holds a stable mental model, task is anomaly detection",
    "A4": "acts on a single viewing, under time pressure, no follow-up questions possible",
    "A5": "holds a strong prior belief, will scrutinize for confirming/disconfirming evidence",
    "A6": "receives the chart embedded in a document, forms first interpretation from chart alone",
}
GOAL = {
    "G1": "establish whether a directional change over time is monotonic, interrupted, or cyclical",
    "G2": "determine which discrete category has the largest/smallest value on a measure",
    "G3": "understand how values are distributed across a full range",
    "G4": "support a binary/multi-option choice, make the decision-relevant difference immediate",
    "G5": "identify whether variables move together, independently, or in opposition",
    "G6": "verify whether a value falls within or outside a pre-specified acceptable range",
}


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")

    packets = json.loads(db.get_memory("kenji", "sprint14_registrar_packets"))
    scenarios = json.loads(db.get_memory("kenji", "sprint13_scenarios_structured"))

    rng = random.Random(99)  # Ingrid's own selection, independent of Kenji's process
    sample_ids = rng.sample(sorted(packets), 4)

    items_block = ""
    for sid in sample_ids:
        sc = scenarios[sid]
        pk = packets[sid]
        forms_block = "\n".join(
            f"  {label}: {v['mark_type']}" for label, v in pk["labeled_candidates"].items()
        )
        items_block += (
            f"\n\n=== {sid} ===\n"
            f"Data: {sc['data_description']}\n"
            f"Audience: {AUDIENCE[sc['audience']]}\n"
            f"Goal: {GOAL[sc['goal']]}\n"
            f"Candidates:\n{forms_block}"
        )

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Spot-check Draco candidate sets before Registrar receives them",
        description=f"Ingrid's own random sample: {sample_ids}",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=3000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "For each of these 4 scenarios (my own random sample, "
            "independent of Kenji's process), check whether EACH candidate "
            "form actually passes F1/F2/F3 (structurally valid, no "
            "explicit constraint violation, is a real commitment) given "
            "the scenario's data/audience/goal. Draco selected these by "
            "constraint-satisfaction cost, which is related to but not "
            "identical to F1/F2/F3 -- a low-cost Draco completion is not "
            "automatically an F1/F2/F3 pass, verify it directly.\n\n"
            "For each candidate in each scenario: PASS or FAIL on F1/F2/F3, "
            "one line each. If any candidate fails, name which check and "
            "why -- that candidate should not have been included in the "
            "set handed to the Registrar.\n\n"
            f"{items_block}\n"
        )}],
    )

    check = result.text
    db.log_usage("ingrid", result.input_tokens, result.output_tokens)

    db.set_memory("ingrid", "sprint14_candidateset_spotcheck", check)
    db.update_task(
        task_id, status="completed", result=check,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/sprint14_candidateset_spotcheck"},
    )

    print(f"[{NAME}] Spot-check sample: {sample_ids}\n\n{check}")
    print(f"\n\n--- stored as ingrid/sprint14_candidateset_spotcheck ---")


if __name__ == "__main__":
    run()
