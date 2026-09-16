"""A fresh Registrar instance (per Sophie's Phase 0 ruling -- symmetric
with the fresh-data-collection independence rule) produces the audience-
optimal ranking for all 20 scenarios, sealed before any model output
exists. Per Kenji's Phase 0 protocol Section 3/4: the Registrar receives
only the scenario data/audience/goal and the labeled candidate forms
(Draco's cost order hidden), ranks by audience fit with a one-sentence
audience-grounded rationale per position, and flags NOTED-CLOSE-CALL when
rank 1/2 turn on the same primary A-or-G dimension.

REAL, DISCLOSED DEVIATION from Section 1's fixed-4-candidate framing:
the protocol was written assuming exactly 4 candidates per scenario
(hence its "25% random baseline" math). The systematic F1/F2/F3 filter
that ran after Phase 0 was gated found variable candidate counts per
scenario (1 to 6), and the founder's middle-path ruling (2026-09-16)
locked in 18 main-analysis scenarios with 2-6 candidates each plus 2
exploratory-only scenarios (S07, S16) with exactly 1 candidate each --
nothing to genuinely rank. This script ranks whatever candidates a
scenario actually has (skipping the ranking call entirely for a
1-candidate scenario, since there is no ordering decision to make) and
records the real per-scenario random baseline (1/N) rather than
asserting a uniform 25% that no longer holds. This deviation is flagged
explicitly for Ingrid's compliance review, not silently absorbed --
Section 1's math needs a documented amendment, which is Ingrid/Sophie's
call, not something decided here.

One real LLM call per scenario (not batched) -- ranking quality is a
content judgment, same reasoning the per-scenario loops elsewhere in
this sprint (backlog38_candidate_filter.py, the redesign script) already
established is needed.
"""
import json
import os
import re

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.registrar.persona import NAME, SYSTEM_PROMPT
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


def _rank_one(client, sid: str, sc: dict, packet: dict) -> dict:
    labeled = packet["labeled_candidates"]
    forms_block = "\n".join(
        f"{label} = {v['mark_type']} (encodes: "
        f"{', '.join((e.get('field') or '(unnamed)') + ' on ' + str(e.get('channel')) for e in v['encodings'])})"
        for label, v in labeled.items()
    )
    n = len(labeled)
    result = stream_complete(
        client, model=MODEL, max_tokens=2000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            f"Scenario {sid}. Rank these {n} candidate forms by audience fit, "
            "per your Sprint 14 ranking task (Phase 0 protocol Section 3). "
            "Rank 1 = most audience-optimal.\n\n"
            f"Data: {sc['data_description']}\n"
            f"Audience ({sc['audience']}): {AUDIENCE[sc['audience']]}\n"
            f"Goal ({sc['goal']}): {GOAL[sc['goal']]}\n\n"
            f"Candidate forms:\n{forms_block}\n\n"
            "For each rank position, one sentence of audience-grounded "
            "rationale -- must reference the audience or goal descriptor "
            "explicitly, not just data-structural properties. If rank 1 "
            "and rank 2's rationales turn on the same primary audience-or-"
            "goal dimension (differing only on a secondary property), flag "
            "it as a NOTED-CLOSE-CALL.\n\n"
            "Return ONLY this JSON, no prose, no fences:\n"
            '{"ranking": [{"rank": 1, "label": "Form X", "rationale": "..."}, '
            '...], "noted_close_call": true|false, '
            '"close_call_note": "..."|null}'
        )}],
    )
    db.log_usage("registrar", result.input_tokens, result.output_tokens)
    raw = re.sub(r"^```(?:json)?|```$", "", result.text.strip(), flags=re.M).strip()
    return json.loads(raw)


def run() -> None:
    require_tool("registrar", "write_preregistration")
    db.set_memory("registrar", "status", "online")

    scenarios = json.loads(db.get_memory("kenji", "sprint13_scenarios_structured"))
    redesigns = json.loads(db.get_memory("kenji", "sprint14_scenario_redesigns"))
    packets = json.loads(db.get_memory("kenji", "sprint14_registrar_packets"))

    # Redesigned scenarios (S03/S07/S14/S16) use the new data_description,
    # not the original -- the Registrar must see the same scenario the
    # candidates were generated from.
    scenario_context = dict(scenarios)
    for sid, r in redesigns.items():
        scenario_context[sid] = {"cell": r["cell"], "audience": r["audience"],
                                  "goal": r["goal"], "data_description": r["data_description"]}

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="registrar",
        title="Sprint 14: audience-optimal rankings for all 20 scenarios",
        description="Fresh Registrar instance, sealed before any model output exists.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    rankings = {}
    baseline_note = {}
    for sid in sorted(packets):
        n = len(packets[sid]["labeled_candidates"])
        if n <= 1:
            only_label = next(iter(packets[sid]["labeled_candidates"]))
            rankings[sid] = {
                "ranking": [{"rank": 1, "label": only_label,
                             "rationale": "Only one F1/F2/F3-valid candidate exists for "
                             "this scenario -- no ranking decision to make. Retained as "
                             "exploratory-only; not part of the FVBS main analysis."}],
                "noted_close_call": False, "close_call_note": None,
                "degenerate_single_candidate": True,
            }
            print(f"[{NAME}] {sid}: single-candidate scenario, no ranking needed (exploratory-only).")
        else:
            rankings[sid] = _rank_one(client, sid, scenario_context[sid], packets[sid])
            rankings[sid]["degenerate_single_candidate"] = False
            cc = " [NOTED-CLOSE-CALL]" if rankings[sid]["noted_close_call"] else ""
            top = rankings[sid]["ranking"][0]
            print(f"[{NAME}] {sid} ({n} candidates): rank 1 = {top['label']}{cc}")
        baseline_note[sid] = f"1/{n} = {round(100/n, 1)}% random baseline (n={n} candidates)"

    db.set_memory("registrar", "sprint14_rankings", json.dumps(rankings, indent=2, ensure_ascii=False))
    db.set_memory("registrar", "sprint14_ranking_baselines", json.dumps(baseline_note, indent=2, ensure_ascii=False))

    n_close_calls = sum(1 for r in rankings.values() if r.get("noted_close_call"))
    n_degenerate = sum(1 for r in rankings.values() if r.get("degenerate_single_candidate"))
    summary = (
        f"20/20 scenarios ranked ({n_degenerate} degenerate single-candidate, "
        f"exploratory-only). {n_close_calls} NOTED-CLOSE-CALL flags raised for "
        f"Ingrid's gate review. Real deviation from Section 1's fixed-25%-"
        f"baseline framing: baselines are per-scenario (1/N), N ranges 1-6 -- "
        f"see registrar/sprint14_ranking_baselines."
    )
    print(f"\n[{NAME}] {summary}")

    db.update_task(
        task_id, status="completed", result=summary,
        artifact_type="ranking",
        artifact_payload={"memory_key": "registrar/sprint14_rankings"},
    )
    print("--- stored as registrar/sprint14_rankings, registrar/sprint14_ranking_baselines ---")


if __name__ == "__main__":
    run()
