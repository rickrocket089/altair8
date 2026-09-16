"""Sprint 14, Phase 2 -> scoring handoff: anonymize the 180 real outputs
for the Blind Scorer, and regenerate the single-recommendation Draco
ground truth the (unchanged, per protocol Section 6) probe scoring needs.

Pure mechanical Python, no LLM -- same discipline as Sprint 13's
anonymization (built ad hoc in that earlier part of this session, not
saved as a file; saved properly here so it's reproducible and reviewable,
same fix already applied once this sprint to the Registrar packets).

Three outputs:
- kenji/sprint14_phase2_formmatch_items: 120 BASELINE+ORDER-BEFORE items
  (anon_id, scenario_text, output) -- the scenario_text is identical
  across BASELINE/ORDER-BEFORE for a given scenario, so it reveals
  nothing about condition. NO model/condition label attached.
- kenji/sprint14_phase2_probe_items: 60 PROBE items (anon_id, output,
  scenario_id_for_groundtruth_lookup_ONLY) -- schema-only, matching
  Sprint 13's format exactly.
- kenji/sprint14_phase2_anon_map: PRIVATE. anon_id -> real
  {scenario_id, condition, model}. The Blind Scorer never reads this key
  (not in its permitted tools) -- kept for de-anonymizing after scoring
  locks, same as Sprint 13.

Draco single-recommendation ground truth (kenji/sprint14_draco_groundtruth):
regenerated fresh via tools.draco_groundtruth.get_draco_recommendation()
for all 20 scenarios, using the REDESIGNED field_spec for S03/S07/S14/S16
(the probe prompts sent in Phase 2 used the redesigned data_description
for those 4, so the ground truth must match what was actually asked).
"""
import json
import os
import random

from dotenv import load_dotenv

from agents.permissions import require_tool
from agents.researcher.persona import NAME
from tools import db
from tools import draco_groundtruth as draco

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

AUDIENCE = {
    "A1": "Your audience is familiar with the measurement domain, but unfamiliar with this specific dataset -- they have no prior hypothesis about its shape or direction.",
    "A2": "Your audience has no domain vocabulary, but is accustomed to interpreting quantitative comparisons in everyday contexts (news media, public health communications, consumer reports).",
    "A3": "Your audience monitors this same metric repeatedly over time and holds a stable mental model of its typical range and variability -- their task is anomaly detection against that expectation.",
    "A4": "Your audience will act on the output of a single viewing, under time pressure, without ability to ask follow-up questions.",
    "A5": "Your audience holds a strong prior belief about the expected finding and will scrutinize the chart for evidence consistent or inconsistent with that belief.",
    "A6": "Your audience receives the chart embedded in a larger document and will not read surrounding text before forming a first interpretation.",
}
GOAL = {
    "G1": "Your goal is to help the audience establish whether a directional change over ordered time points is monotonic, interrupted, or cyclical.",
    "G2": "Your goal is to help the audience determine which of several discrete categories has the largest or smallest value on a single measure.",
    "G3": "Your goal is to help the audience understand how values are distributed across a full range, including where the bulk of observations fall and how spread out they are.",
    "G4": "Your goal is to support a binary or multi-option choice by making the decision-relevant difference between options perceptually immediate.",
    "G5": "Your goal is to help the audience identify whether two or more variables move together, independently, or in opposition across observations.",
    "G6": "Your goal is to help the audience verify that a value or set of values falls within or outside a pre-specified acceptable range.",
}


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    raw = json.loads(db.get_memory("kenji", "sprint14_phase2_raw"))
    scenarios = json.loads(db.get_memory("kenji", "sprint13_scenarios_structured"))
    redesigns = json.loads(db.get_memory("kenji", "sprint14_scenario_redesigns"))
    field_extraction = json.loads(db.get_memory("kenji", "sprint13_field_extraction"))

    scenario_context = dict(scenarios)
    for sid, r in redesigns.items():
        scenario_context[sid] = {"cell": r["cell"], "audience": r["audience"],
                                  "goal": r["goal"], "data_description": r["data_description"]}
    field_spec_context = dict(field_extraction)
    for sid, r in redesigns.items():
        field_spec_context[sid] = r["field_spec"]

    # --- Regenerate Draco single-recommendation ground truth (probe scoring) ---
    groundtruth = {}
    for sid, spec in field_spec_context.items():
        groundtruth[sid] = draco.get_draco_recommendation(spec, seed=0)
        print(f"[{NAME}] Draco groundtruth {sid}: {groundtruth[sid]['mark_type']}")
    db.set_memory("kenji", "sprint14_draco_groundtruth", json.dumps(groundtruth, indent=2, default=str, ensure_ascii=False))

    # --- Anonymize ---
    rng = random.Random("sprint14-anon")
    formmatch_items = []
    probe_items = []
    anon_map = {}
    anon_id_counter = 0

    formmatch_pool = [r for r in raw if r["condition"] in ("BASELINE", "ORDER-BEFORE")]
    probe_pool = [r for r in raw if r["condition"] == "PROBE"]
    rng.shuffle(formmatch_pool)
    rng.shuffle(probe_pool)

    for r in formmatch_pool:
        sc = scenario_context[r["scenario_id"]]
        scenario_text = (
            f"{sc['data_description']}\n\n{AUDIENCE[sc['audience']]}\n\n{GOAL[sc['goal']]}"
        )
        formmatch_items.append({
            "anon_id": anon_id_counter,
            "scenario_text": scenario_text,
            "output": r["output"],
            "scenario_id_for_groundtruth_lookup_ONLY": r["scenario_id"],
        })
        anon_map[anon_id_counter] = {
            "scenario_id": r["scenario_id"], "condition": r["condition"], "model": r["model"],
        }
        anon_id_counter += 1

    for r in probe_pool:
        probe_items.append({
            "anon_id": anon_id_counter,
            "output": r["output"],
            "scenario_id_for_groundtruth_lookup_ONLY": r["scenario_id"],
        })
        anon_map[anon_id_counter] = {
            "scenario_id": r["scenario_id"], "condition": r["condition"], "model": r["model"],
        }
        anon_id_counter += 1

    assert len(formmatch_items) == 120, f"expected 120 formmatch items, got {len(formmatch_items)}"
    assert len(probe_items) == 60, f"expected 60 probe items, got {len(probe_items)}"
    assert len(anon_map) == 180

    db.set_memory("kenji", "sprint14_phase2_formmatch_items", json.dumps(formmatch_items, indent=2, ensure_ascii=False))
    db.set_memory("kenji", "sprint14_phase2_probe_items", json.dumps(probe_items, indent=2, ensure_ascii=False))
    # PRIVATE -- Blind Scorer's permitted tools do not include reading this key.
    db.set_memory("kenji", "sprint14_phase2_anon_map", json.dumps(anon_map, indent=2, ensure_ascii=False))

    print(f"\n[{NAME}] Anonymized: {len(formmatch_items)} formmatch items, "
          f"{len(probe_items)} probe items. anon_map stored privately "
          f"(kenji/sprint14_phase2_anon_map -- not in blind_scorer's permitted tools).")
    print("--- stored as kenji/sprint14_phase2_formmatch_items, "
          "kenji/sprint14_phase2_probe_items, kenji/sprint14_phase2_anon_map, "
          "kenji/sprint14_draco_groundtruth ---")


if __name__ == "__main__":
    run()
