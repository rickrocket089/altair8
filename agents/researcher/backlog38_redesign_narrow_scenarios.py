"""Sprint 14, middle path (founder's decision 2026-09-16): the systematic
F1/F2/F3 filter (backlog38_candidate_filter.py) left 4/20 scenarios with
only a single valid Draco candidate -- S03 (A5xG4), S07 (A4xG1), S14
(A1xG5), S16 (A4xG5). Rather than exclude them (path 1) or redesign the
whole scenario set (path 2), the founder chose to repair only these 4.

The audience x goal cell for each is a fixed experimental-design slot and
must not change -- only the underlying data (domain, variable count/types,
described pattern) may be redesigned, so structurally more mark types
become genuinely F1/F2/F3-viable while the audience/goal reasoning task
stays just as hard as it was.

Real diagnostic pulled from the filter's own recorded reasons before
writing this prompt (not guessed):
- S03: 5 simultaneous fields (2 categorical + 3 continuous, including two
  CI-bound fields) crowd out nearly every mark type except point.
- S07: two continuous measures (MAP, heart rate) plotted jointly over an
  ordered time axis under a time-pressure audience (A4) leaves only line
  viable -- structurally a dual-trajectory-over-time problem.
- S14 / S16: exactly two continuous fields per unordered nominal entity is
  the textbook scatterplot case -- G5 (covariation) over that exact shape
  is structurally answerable only by point. Both need a genuine structural
  change (an ordering, a grouping, or a third dimension), not a rewording.

One call per scenario (not batched) -- this is real generative design work
per item, the same reasoning quality backlog38_candidate_filter.py's
per-scenario loop already established is needed for content judgments here.
"""
import json
import os
import re

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db
from tools import draco_groundtruth as draco
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

RUBRIC = """F1/F2/F3, applied per candidate mark type:
F1 (structurally valid): given the stated goal, could a technically
competent version of this mark type convey the goal's target pattern?
F2 (no explicit constraint violation): does the audience descriptor state
an explicit constraint this mark type directly violates?
F3 (real commitment): can this mark type commit to a specific claim, or is
it inherently ambiguous/decorative for this data?
A mark type PASSES only if it passes all three."""

TARGET_SIDS = ["S03", "S07", "S14", "S16"]

FIELD_TYPE_GUIDE = """TYPE MUST BE ONE OF FOUR VALUES:
- 'nominal': categories with no inherent order.
- 'ordinal_or_temporal': a sequence with meaningful order (years, months,
  weeks, any time-indexed axis, or an explicitly ordered category).
- 'continuous': a numeric measure with no inherent grouping.
- 'boolean': exactly two states.
approximate_cardinality: integer if the description states or implies one
(e.g. number of categories, number of rows), else null."""


def _redesign_one(client, sid: str, sc: dict, old_field_spec: dict, fail_reasons: list[dict]) -> dict:
    fail_block = "\n".join(
        f"- {c['mark_type']}: {c.get('reason_if_fail') or '(passed)'}"
        for c in fail_reasons
    )
    result = stream_complete(
        client, model=MODEL, max_tokens=2500, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Sprint 14 (Backlog #38), middle-path repair. This scenario "
            f"({sid}, audience x goal cell {sc['cell']}) was left with only "
            "1 valid Draco candidate mark type after the real F1/F2/F3 "
            "filter -- almost every mark type was structurally incapable "
            "of serving this exact data shape, not a filter bug.\n\n"
            f"Audience ({sc['audience']}): {AUDIENCE[sc['audience']]}\n"
            f"Goal ({sc['goal']}): {GOAL[sc['goal']]}\n\n"
            f"{RUBRIC}\n\n"
            "ORIGINAL DATA DESCRIPTION (for context on domain flavor only "
            "-- you are replacing this, not patching it):\n"
            f"{sc['data_description']}\n\n"
            f"ORIGINAL FIELD SPEC:\n{json.dumps(old_field_spec, indent=2)}\n\n"
            "WHY IT FAILED (real recorded reasons from the filter, one per "
            "mark type):\n"
            f"{fail_block}\n\n"
            "TASK: design a REPLACEMENT scenario for this exact audience x "
            "goal cell. HARD CONSTRAINTS:\n"
            "1. The audience and goal semantics above are fixed -- do not "
            "make the reasoning task easier or change what's being tested.\n"
            "2. Change the underlying data structure (variable count, "
            "types, whether an ordering/grouping dimension exists) so that "
            "AT LEAST 4 of the 7 mark types (point, bar, line, area, text, "
            "tick, rect) can plausibly pass F1/F2/F3 for this scenario -- "
            "not just be Draco-satisfiable, genuinely structurally capable "
            "given the reasons above.\n"
            "3. Keep it a real, plausible domain scenario -- not a toy "
            "example built just to satisfy the filter.\n"
            "4. Pick a NEW domain (not the same one as the original) so "
            "this doesn't read as a cosmetic patch.\n\n"
            f"{FIELD_TYPE_GUIDE}\n\n"
            "Return ONLY this JSON object, no prose, no fences:\n"
            "{\n"
            '  "data_description": "... (same style as the original: '
            'Domain / Variables / Pattern) ...",\n'
            '  "field_spec": {"number_rows": int, "fields": '
            '[{"field_name": str, "type": str, "approximate_cardinality": '
            "int|null}, ...]},\n"
            '  "rationale": "1-3 sentences: which structural change opens '
            'up which additional mark types, and why the audience/goal '
            'difficulty is unchanged"\n'
            "}"
        )}],
    )
    db.log_usage("kenji", result.input_tokens, result.output_tokens)
    raw = re.sub(r"^```(?:json)?|```$", "", result.text.strip(), flags=re.M).strip()
    return json.loads(raw)


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    scenarios = json.loads(db.get_memory("kenji", "sprint13_scenarios_structured"))
    field_extraction = json.loads(db.get_memory("kenji", "sprint13_field_extraction"))
    filter_results = json.loads(db.get_memory("kenji", "sprint14_candidate_f123_filter"))
    final_candidates = json.loads(db.get_memory("kenji", "sprint14_final_candidatesets"))

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 14 middle-path: redesign the 4 single-candidate scenarios",
        description=f"Founder's decision: repair {TARGET_SIDS} only, other 16 untouched.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    redesigns = {}
    for sid in TARGET_SIDS:
        sc = scenarios[sid]
        redesign = _redesign_one(client, sid, sc, field_extraction[sid], filter_results[sid])
        redesigns[sid] = {
            "cell": sc["cell"], "audience": sc["audience"], "goal": sc["goal"],
            "data_description": redesign["data_description"],
            "field_spec": redesign["field_spec"],
            "rationale": redesign["rationale"],
        }
        print(f"[{NAME}] {sid} redesigned. Rationale: {redesign['rationale']}")

    db.set_memory("kenji", "sprint14_scenario_redesigns", json.dumps(redesigns, indent=2, ensure_ascii=False))

    # Regenerate Draco candidate sets for the 4 redesigned scenarios, real
    # calls through the same tool the original 20 used.
    new_candidatesets = {}
    for sid, r in redesigns.items():
        new_candidatesets[sid] = draco.get_draco_candidate_set(r["field_spec"], n_candidates=4, seed=0)
        n_sat = sum(1 for t in new_candidatesets[sid]["all_mark_types_tested"] if t["satisfiable"])
        print(f"[{NAME}] {sid} redesigned Draco pass: {n_sat}/7 mark types satisfiable "
              f"({[t['mark_type'] for t in new_candidatesets[sid]['all_mark_types_tested'] if t['satisfiable']]})")

    db.set_memory("kenji", "sprint14_redesign_draco_candidatesets", json.dumps(new_candidatesets, indent=2, default=str, ensure_ascii=False))

    # Rerun the real F1/F2/F3 filter, same rubric, on just these 4.
    new_filter_results = {}
    for sid, r in redesigns.items():
        satisfiable_types = [t["mark_type"] for t in new_candidatesets[sid]["all_mark_types_tested"] if t["satisfiable"]]
        types_block = "\n".join(f"- {mt}" for mt in satisfiable_types)
        result = stream_complete(
            client, model=MODEL, max_tokens=2500, system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": (
                f"{RUBRIC}\n\n"
                f"Scenario: {r['data_description']}\n"
                f"Audience: {AUDIENCE[r['audience']]}\n"
                f"Goal: {GOAL[r['goal']]}\n\n"
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
        raw = re.sub(r"^```(?:json)?|```$", "", result.text.strip(), flags=re.M).strip()
        checks = json.loads(raw)
        new_filter_results[sid] = checks
        n_pass = sum(1 for c in checks if c["overall"] == "PASS")
        print(f"[{NAME}] {sid} redesigned F1/F2/F3: {n_pass}/{len(checks)} pass "
              f"({[c['mark_type'] for c in checks if c['overall']=='PASS']})")

    db.set_memory("kenji", "sprint14_redesign_f123_filter", json.dumps(new_filter_results, indent=2, ensure_ascii=False))

    # Merge into the final candidate sets: 16 originals untouched, 4 replaced.
    merged = dict(final_candidates)
    for sid in TARGET_SIDS:
        checks = new_filter_results[sid]
        pass_types = {c["mark_type"] for c in checks if c["overall"] == "PASS"}
        all_tested = new_candidatesets[sid]["all_mark_types_tested"]
        valid_ranked = [t for t in all_tested if t["satisfiable"] and t["mark_type"] in pass_types]
        valid_ranked.sort(key=lambda t: t["cost"])
        top = valid_ranked[:4]
        merged[sid] = {
            "valid_candidates": top,
            "n_valid_total": len(valid_ranked),
            "encoded_fields": new_candidatesets[sid]["encoded_fields"],
            "main_analysis_eligible": len(top) >= 2,
            "redesigned": True,
        }

    db.set_memory("kenji", "sprint14_final_candidatesets_v2", json.dumps(merged, indent=2, default=str, ensure_ascii=False))

    n_short = sum(1 for v in merged.values() if len(v["valid_candidates"]) < 4)
    n_excluded = sum(1 for v in merged.values() if not v["main_analysis_eligible"])
    still_single = [sid for sid in TARGET_SIDS if merged[sid]["n_valid_total"] <= 1]
    summary = (
        f"Redesigned {TARGET_SIDS}. After redesign+refilter: "
        f"{n_short}/20 scenarios still short of 4 valid candidates, "
        f"{n_excluded}/20 excluded from main analysis (<2 valid). "
        f"Still single-candidate after redesign: {still_single or 'none'}."
    )
    print(f"\n[{NAME}] {summary}")

    db.update_task(
        task_id, status="completed", result=summary,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/sprint14_final_candidatesets_v2"},
    )
    print("--- stored as kenji/sprint14_scenario_redesigns, "
          "kenji/sprint14_redesign_draco_candidatesets, "
          "kenji/sprint14_redesign_f123_filter, "
          "kenji/sprint14_final_candidatesets_v2 ---")


if __name__ == "__main__":
    run()
