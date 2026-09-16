"""Sprint 14: real F1/F2/F3 filter over Draco's candidate mark types,
before the top-N selection that gets handed to the Registrar.

Real finding that made this necessary (Ingrid's spot-check, 2026-09-16):
Draco's own cost-based ranking is a schema-structural constraint
optimization, not a check against this project's F1/F2/F3 definition
(which requires the form to serve the STATED communicative purpose, not
just be schema-compatible). 7/16 candidates (44%) in a 4-scenario sample
failed F1 or F2 despite being Draco-satisfiable. This runs the same check
Ingrid did by hand, systematically, for all 20 scenarios x up to 7 mark
types each, before finalizing which candidates reach the Registrar.
"""
import json
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
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

RUBRIC = """F1/F2/F3, applied per candidate mark type (not a full model output --
just: could this form type, well-executed, serve this scenario?):

F1 (structurally valid): given the stated goal, could a technically
competent version of this mark type convey the goal's target pattern
(trajectory shape, distribution spread, magnitude comparison, etc. as the
goal requires)? Not "is it the best form" -- "is it structurally CAPABLE."
F2 (no explicit constraint violation): does the audience descriptor state
an explicit constraint (time pressure requiring single-glance immediacy,
no domain vocabulary, etc.) that this mark type directly violates?
F3 (real commitment): can this mark type commit to a specific claim, or is
it inherently ambiguous/decorative for this data?
A mark type PASSES only if it passes all three."""


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    packets = json.loads(db.get_memory("kenji", "sprint14_registrar_packets"))
    scenarios = json.loads(db.get_memory("kenji", "sprint13_scenarios_structured"))
    candidatesets = json.loads(db.get_memory("kenji", "sprint14_draco_candidatesets"))

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 14: F1/F2/F3 filter over all Draco candidate mark types",
        description="Systematic version of Ingrid's spot-check finding -- required before Registrar starts.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    filter_results = {}

    for sid in sorted(scenarios):
        sc = scenarios[sid]
        all_tested = candidatesets[sid]["all_mark_types_tested"]
        satisfiable_types = [t["mark_type"] for t in all_tested if t["satisfiable"]]

        types_block = "\n".join(f"- {mt}" for mt in satisfiable_types)
        result = stream_complete(
            client, model=MODEL, max_tokens=2500, system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": (
                f"{RUBRIC}\n\n"
                f"Scenario: {sc['data_description']}\n"
                f"Audience: {AUDIENCE[sc['audience']]}\n"
                f"Goal: {GOAL[sc['goal']]}\n\n"
                f"Check each of these Draco-satisfiable mark types against "
                f"F1/F2/F3 for this specific scenario:\n{types_block}\n\n"
                "Return ONLY a JSON array: [{\"mark_type\": \"...\", "
                "\"f1\": \"pass\"|\"fail\", \"f2\": \"pass\"|\"fail\", "
                "\"f3\": \"pass\"|\"fail\", \"overall\": \"PASS\"|\"FAIL\", "
                "\"reason_if_fail\": \"...\"|null}, ...]. "
                "One entry per mark type listed. No prose, no fences."
            )}],
        )
        db.log_usage("kenji", result.input_tokens, result.output_tokens)
        import re
        raw = re.sub(r"^```(?:json)?|```$", "", result.text.strip(), flags=re.M).strip()
        checks = json.loads(raw)
        filter_results[sid] = checks
        n_pass = sum(1 for c in checks if c["overall"] == "PASS")
        print(f"[{NAME}] {sid}: {n_pass}/{len(checks)} pass F1/F2/F3 "
              f"({[c['mark_type'] for c in checks if c['overall']=='PASS']})")

    db.set_memory("kenji", "sprint14_candidate_f123_filter", json.dumps(filter_results, indent=2, ensure_ascii=False))

    # Rebuild the final candidate sets: valid types only, ranked by Draco cost, top 4
    final_candidates = {}
    for sid in sorted(scenarios):
        checks = filter_results[sid]
        pass_types = {c["mark_type"] for c in checks if c["overall"] == "PASS"}
        all_tested = candidatesets[sid]["all_mark_types_tested"]
        valid_ranked = [t for t in all_tested if t["satisfiable"] and t["mark_type"] in pass_types]
        valid_ranked.sort(key=lambda t: t["cost"])
        top = valid_ranked[:4]
        final_candidates[sid] = {
            "valid_candidates": top,
            "n_valid_total": len(valid_ranked),
            "encoded_fields": candidatesets[sid]["encoded_fields"],
            "main_analysis_eligible": len(top) >= 2,  # Sophie's rule: <2 valid -> excluded, exploratory only
        }

    db.set_memory("kenji", "sprint14_final_candidatesets", json.dumps(final_candidates, indent=2, default=str, ensure_ascii=False))

    n_short = sum(1 for v in final_candidates.values() if len(v["valid_candidates"]) < 4)
    n_excluded = sum(1 for v in final_candidates.values() if not v["main_analysis_eligible"])
    print(f"\n[{NAME}] Filter complete. {n_short}/20 scenarios have <4 valid candidates after filtering. "
          f"{n_excluded}/20 excluded from main analysis (< 2 valid).")

    db.update_task(
        task_id, status="completed",
        result=f"{n_short}/20 scenarios short of 4 valid candidates; {n_excluded} excluded from main analysis.",
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/sprint14_final_candidatesets"},
    )
    print("--- stored as kenji/sprint14_final_candidatesets ---")


if __name__ == "__main__":
    run()
