"""Applies Ingrid's gate review findings to the stored FVBS scores
(ingrid/sprint14_fvbs_gate_review), real corrections found while
verifying her review before letting statistics run on this data:

1. Her 9 AMBIGUOUS_ESCALATE resolutions (Task 1 of the gate review):
   2 -> FULL_PASS, 4 -> FVBS, 3 -> NOT_IN_SET (anon_id=50/S08 kept as
   NOT_IN_SET with an explicit compositionality-limit annotation, per
   her call -- COMPOSITE sub-category left as a founder/Sophie decision,
   not created unilaterally here).

2. A THIRD real scoring error found while checking her Condition 2 (had
   she seen the actual nominated forms for S11/S14/S19's NOT_IN_SET
   trials, which she flagged she could not assess from the gate-review
   brief alone): 3 of S14's NOT_IN_SET trials (anon_id 70/91/106) all
   explicitly nominate a LINE chart ("dual-line time series", "dual-axis
   line chart with small multiples", "small-multiple dual-axis line
   charts") -- and S14's candidate set DOES include line (Form A). This
   directly contradicts the matching glossary's own already-established
   rule (small multiples/dual-axis = layout, not a mark-family change --
   the same rule correctly applied to bar in Sprint 14's Phase 1
   assessment and to point elsewhere in this same scoring pass, e.g.
   S14 anon_id=11/107 "small-multiple connected scatterplot" -> point).
   This is a genuine scorer inconsistency (Step 2 matching), not a
   vocabulary-ceiling or candidate-set-construction issue like S03/S20.
   Corrected deterministically: matched to Form A (line), rank per the
   locked S14 ranking, final_outcome recombined the same way
   fix_fvbs_combination_bug.py already established.

S20's NOT_IN_SET cases are explicitly NOT touched by this script --
verified separately (real Draco costs: line=87 vs. the top-4 cutoff at
rect=76) as a genuine cost-ranking exclusion, not a bug. Documented as
its own, distinct phenomenon.
"""
import json

from agents.permissions import require_tool
from agents.blind_scorer.persona import NAME
from tools import db

ESCALATION_RESOLUTIONS = {
    2:  {"match_outcome": "matched", "matched_label": "Form B", "note": "dot plot + reference band -- band is ancillary, point (S04 Form B) is primary"},
    59: {"match_outcome": "matched", "matched_label": "Form A", "note": "bullet/lollipop reading -> bar family (S04 Form A); Ingrid's Task 1"},
    4:  {"match_outcome": "matched", "matched_label": "Form C", "note": "beeswarm = point + jitter transform (S06 Form C); Ingrid's Task 1"},
    33: {"match_outcome": "matched", "matched_label": "Form C", "note": "beeswarm + medians, consistent with anon_id=4 (S06 Form C)"},
    26: {"match_outcome": "matched", "matched_label": "Form A", "note": "slope graph = line mark (S07 Form A); only candidate, correct"},
    50: {"match_outcome": "not_in_set", "matched_label": None, "note": "COMPOSITIONALITY LIMIT, not vocabulary ceiling -- co-equal dual-panel (line+area vs bar), both mark families individually in Draco's vocabulary but the composite can't reduce to one label. Flagged for Sophie: COMPOSITE sub-category decision needed."},
    17: {"match_outcome": "not_in_set", "matched_label": None, "note": "dumbbell/connected-dot, consistent with S03 vocabulary-ceiling ruling"},
    1:  {"match_outcome": "matched", "matched_label": "Form A", "note": "line primary (S16 Form A); filled difference area is a meaningful secondary encoding not in the 1-candidate set, but per Ingrid FVBS not NOT_IN_SET"},
    19: {"match_outcome": "not_in_set", "matched_label": None, "note": "primary nomination is a line chart; line absent from S20 candidate set (real cost-ranking exclusion, verified separately, not a bug)"},
}

S14_MATCHING_FIX = {
    70: "Form A",   # "dual-line time series ... with added divergence band"
    91: "Form A",   # "dual-axis line chart with small multiples by zone"
    106: "Form A",  # "Small-multiple dual-axis line charts"
}


def _combine_final_outcome(s: dict) -> str:
    struct_pass = s["f1"] == "not_met" and s["f2"] == "not_met" and s["f3"] == "not_met"
    if s["match_outcome"] == "ambiguous_escalate":
        return "AMBIGUOUS_ESCALATE"
    if not struct_pass:
        return "STRUCTURAL_FAIL"
    if s["match_outcome"] == "not_in_set":
        return "NOT_IN_SET"
    if s["match_outcome"] == "matched":
        return "FULL_PASS" if s["rank"] == 1 else "FVBS"
    raise ValueError(f"unhandled score record: {s}")


def run() -> None:
    require_tool("blind_scorer", "write_score")

    scores = {s["anon_id"]: s for s in json.loads(db.get_memory("blind_scorer", "sprint14_fvbs_scores"))}
    packets = json.loads(db.get_memory("kenji", "sprint14_registrar_packets"))
    rankings = json.loads(db.get_memory("registrar", "sprint14_rankings"))
    items = {it["anon_id"]: it for it in json.loads(db.get_memory("kenji", "sprint14_phase2_formmatch_items"))}

    n_resolved = 0
    for anon_id, res in ESCALATION_RESOLUTIONS.items():
        s = scores[anon_id]
        assert s["match_outcome"] == "ambiguous_escalate", f"anon_id={anon_id} was not AMBIGUOUS_ESCALATE"
        sid = items[anon_id]["scenario_id_for_groundtruth_lookup_ONLY"]
        s["match_outcome"] = res["match_outcome"]
        s["matched_label"] = res["matched_label"]
        if res["matched_label"]:
            rank_entry = next(p for p in rankings[sid]["ranking"] if p["label"] == res["matched_label"])
            s["rank"] = rank_entry["rank"]
        else:
            s["rank"] = None
        s["ingrid_resolution_note"] = res["note"]
        s["final_outcome"] = _combine_final_outcome(s)
        n_resolved += 1

    n_fixed = 0
    for anon_id, label in S14_MATCHING_FIX.items():
        s = scores[anon_id]
        s["match_outcome_original"] = s["match_outcome"]
        s["match_outcome"] = "matched"
        s["matched_label"] = label
        rank_entry = next(p for p in rankings["S14"]["ranking"] if p["label"] == label)
        s["rank"] = rank_entry["rank"]
        s["s14_matching_error_fixed"] = True
        s["final_outcome"] = _combine_final_outcome(s)
        n_fixed += 1

    all_scores = list(scores.values())
    db.set_memory("blind_scorer", "sprint14_fvbs_scores", json.dumps(all_scores, indent=2, ensure_ascii=False))

    totals = {}
    for s in all_scores:
        totals[s["final_outcome"]] = totals.get(s["final_outcome"], 0) + 1
    print(f"[{NAME}] Resolved {n_resolved} AMBIGUOUS_ESCALATE trials per Ingrid's gate review.")
    print(f"[{NAME}] Fixed {n_fixed} S14 matching errors (line-chart nominations wrongly scored NOT_IN_SET).")
    print(f"[{NAME}] Final totals: {totals}")


if __name__ == "__main__":
    run()
