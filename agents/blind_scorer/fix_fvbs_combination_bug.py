"""Real bug found and fixed post-hoc, 2026-09-16: score_fvbs.py asked the
scoring LLM to both determine f1/f2/f3 AND synthesize final_outcome in
the same response. Systematic check across all 120 scored trials found
21 where the stated final_outcome contradicted the trial's own f1/f2/f3
sub-judgments: every case where match_outcome="not_in_set" and f1/f2/f3
were all "not_met" (i.e. genuinely structurally valid) got final_outcome
"STRUCTURAL_FAIL" instead of the correct "NOT_IN_SET" -- exactly the
"one failure type must not mask or launder into the other" failure mode
protocol Section 2 explicitly warned against, produced by the scorer
itself rather than avoided by it.

Fix applied: recompute final_outcome DETERMINISTICALLY in Python from
the already-stated, reliable f1/f2/f3/match_outcome/rank fields, rather
than trust the LLM's own combination arithmetic -- the same principle
already applied elsewhere this project (scipy over LLM arithmetic for
statistics). This is not a re-score: no sub-judgment (f1/f2/f3, matched
label, rank) is changed, only the final label that combines them.

After the fix: 0/120 genuine structural failures (all-"not_met" on
f1/f2/f3 across every trial) -- consistent with, not contradicted by,
Sprint 13's own headline finding (0/60 F1/F2/F3 failures), which is the
exact ceiling result that motivated Sprint 14's redesign in the first
place. NOT_IN_SET rose from 11/120 to 32/120 (26.7%), well above the
Registrar's pre-registered 5-20% prediction -- a real, notable finding
for Ingrid's gate review before statistics, not smoothed over.

This script is idempotent: rerunning it after the fix has already been
applied finds 0 further mismatches and changes nothing.
"""
import json

from agents.permissions import require_tool
from agents.blind_scorer.persona import NAME
from tools import db


def _expected_outcome(s: dict) -> str:
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

    scores = json.loads(db.get_memory("blind_scorer", "sprint14_fvbs_scores"))

    n_fixed = 0
    for s in scores:
        expected = _expected_outcome(s)
        if expected != s["final_outcome"]:
            s["final_outcome_original_llm"] = s["final_outcome"]
            s["final_outcome"] = expected
            s["final_outcome_corrected"] = True
            n_fixed += 1
        else:
            s.setdefault("final_outcome_corrected", False)

    db.set_memory("blind_scorer", "sprint14_fvbs_scores", json.dumps(scores, indent=2, ensure_ascii=False))

    totals = {}
    for s in scores:
        totals[s["final_outcome"]] = totals.get(s["final_outcome"], 0) + 1
    n_struct_fail = totals.get("STRUCTURAL_FAIL", 0)
    print(f"[{NAME}] Recomputed {len(scores)} final_outcome labels from stated sub-judgments; "
          f"{n_fixed} corrected this run.")
    print(f"[{NAME}] Totals: {totals}")
    print(f"[{NAME}] Genuine structural failures: {n_struct_fail}/{len(scores)}.")


if __name__ == "__main__":
    run()
