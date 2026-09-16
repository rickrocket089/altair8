"""Sprint 14, Phase 3: real, code-computed statistics on the corrected
FVBS scores -- scipy only (binomtest for proportions/CIs, exact McNemar
via binomtest on discordant pairs), never LLM arithmetic, same principle
Sprint 13 established. Unlike Sprint 13's statistics (computed ad hoc,
never saved as a file, results hand-transcribed into the synthesis
script), this is a real, standalone, rerunnable script -- the same fix
already applied twice this sprint to other steps that were originally
built ad hoc (Registrar packets, anonymization).

Confirmatory FVBS rate is computed over the 18 main-analysis scenarios
only (S07/S16 excluded, per the founder's ruling); NOT-IN-SET rate is
computed over all 20 (S07/S16 included), per protocol Section 4.1.
"""
import json
import os
from collections import defaultdict

from dotenv import load_dotenv
from scipy.stats import binomtest

from agents.permissions import require_tool
from agents.researcher.persona import NAME
from tools import db

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

CONFIRMATORY_EXCLUDED = {"S07", "S16"}
MODELS = ["claude-sonnet-4-6", "gpt-5.2", "gemini-flash-latest"]


def _ci(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    res = binomtest(k, n)
    ci = res.proportion_ci(confidence_level=0.95)
    return (ci.low * 100, ci.high * 100)


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    scores = json.loads(db.get_memory("blind_scorer", "sprint14_fvbs_scores"))
    anon_map = json.loads(db.get_memory("kenji", "sprint14_phase2_anon_map"))
    final_candidates = json.loads(db.get_memory("kenji", "sprint14_final_candidatesets_v3"))
    probe_scores = json.loads(db.get_memory("blind_scorer", "sprint14_probe_scores"))
    probe_items = {it["anon_id"]: it for it in json.loads(db.get_memory("kenji", "sprint14_phase2_probe_items"))}

    for s in scores:
        meta = anon_map[str(s["anon_id"])]
        s["scenario_id"] = meta["scenario_id"]
        s["condition"] = meta["condition"]
        s["model"] = meta["model"]

    lines = []
    lines.append("=== REAL, CODE-COMPUTED STATISTICS (scipy binomtest / exact McNemar on")
    lines.append("discordant pairs -- not LLM-estimated) ===\n")

    # --- 1. NOT-IN-SET rate, all 20 scenarios, all 120 trials ---
    n_total = len(scores)
    n_not_in_set = sum(1 for s in scores if s["final_outcome"] == "NOT_IN_SET")
    lo, hi = _ci(n_not_in_set, n_total)
    lines.append(f"H_NOTINSET -- NOT-IN-SET RATE, all 20 scenarios (pre-registered: 5-20%):")
    lines.append(f"Observed: {n_not_in_set}/{n_total} = {n_not_in_set/n_total:.1%}, 95% CI [{lo:.1f}%,{hi:.1f}%]")
    verdict = "ABOVE the pre-registered range" if n_not_in_set/n_total > 0.20 else (
        "BELOW the pre-registered range" if n_not_in_set/n_total < 0.05 else "WITHIN the pre-registered range")
    lines.append(f"VERDICT: {verdict}. NOTE (per Ingrid's gate review): this rate reflects "
                 "3 distinct, individually-verified phenomena, not one cause -- real Draco-"
                 "vocabulary ceiling, Draco cost-ranking exclusion of a valid candidate (S20), "
                 "and a now-fixed scorer matching error (S14). Do not report as a single "
                 "undifferentiated number without this breakdown.\n")

    # --- 2. Confirmatory FVBS rate, 18 main-analysis scenarios, structurally-valid trials only ---
    confirmatory = [s for s in scores if s["scenario_id"] not in CONFIRMATORY_EXCLUDED]
    valid = [s for s in confirmatory if s["final_outcome"] in ("FULL_PASS", "FVBS")]
    n_fvbs = sum(1 for s in valid if s["final_outcome"] == "FVBS")
    n_valid = len(valid)
    lo, hi = _ci(n_fvbs, n_valid)
    lines.append(f"H_FVBS -- CONFIRMATORY FVBS RATE, 18 main-analysis scenarios, among structurally-")
    lines.append(f"valid (FULL_PASS+FVBS) trials only (pre-registered: 40-65%):")
    lines.append(f"Observed: {n_fvbs}/{n_valid} = {n_fvbs/n_valid:.1%}, 95% CI [{lo:.1f}%,{hi:.1f}%]")
    lines.append(f"(NOT_IN_SET trials excluded from this denominator per protocol Section 2 -- "
                 f"{len(confirmatory)-n_valid} of {len(confirmatory)} confirmatory trials were "
                 f"NOT_IN_SET, structural-fail, or otherwise not in-set)")
    if 0.40 <= n_fvbs/n_valid <= 0.65:
        verdict = "WITHIN the pre-registered 40-65% range"
    elif n_fvbs/n_valid < 0.30:
        verdict = "BELOW 30% -- falsifies the prediction, evidence AGAINST convention-reproduction (genuine audience reasoning signal)"
    elif n_fvbs/n_valid > 0.75:
        verdict = "ABOVE 75% -- falsifies the prediction from above, triggers review of the locked rankings"
    else:
        verdict = "in the 30-39% ambiguous zone the pre-registration flagged as requiring interpretive caution, not falsification"
    lines.append(f"VERDICT: {verdict}\n")

    # --- 2b. Stratified by candidate-set size, per pre-registration's mandatory reporting requirement ---
    lines.append("H_FVBS STRATIFIED BY CANDIDATE-SET SIZE (mandatory per Registrar's pre-registration,")
    lines.append("per-stratum baseline = 1/N, not the aggregate ~32%):")
    by_n = defaultdict(list)
    for s in valid:
        n_cand = final_candidates[s["scenario_id"]]["n_valid_total"]
        n_cand_capped = min(n_cand, 4)  # candidate set itself is capped at top-4
        by_n[n_cand_capped].append(s)
    for n_cand in sorted(by_n):
        stratum = by_n[n_cand]
        n_fvbs_s = sum(1 for s in stratum if s["final_outcome"] == "FVBS")
        lo, hi = _ci(n_fvbs_s, len(stratum))
        baseline = 100 / n_cand
        lines.append(f"  N={n_cand} candidates (random baseline {baseline:.1f}%): "
                     f"{n_fvbs_s}/{len(stratum)} = {n_fvbs_s/len(stratum):.1%} FVBS, "
                     f"95% CI [{lo:.1f}%,{hi:.1f}%]")
    lines.append("")

    # --- 3. ORDER-BEFORE effect, per model, exact McNemar on paired confirmatory trials ---
    lines.append("H_ORDER -- ORDER-BEFORE vs BASELINE FVBS rate, per model, exact McNemar on")
    lines.append("discordant pairs (pre-registered: >=8pp reduction in FVBS rate):")
    by_model_scenario = defaultdict(dict)
    for s in confirmatory:
        by_model_scenario[(s["model"], s["scenario_id"])][s["condition"]] = s

    for model in MODELS:
        pairs = [v for (m, sid), v in by_model_scenario.items() if m == model]
        # Only pairs where BOTH conditions are structurally-valid in-set trials
        # (FULL_PASS or FVBS) are usable for the binary FVBS/FULL_PASS comparison.
        usable = [p for p in pairs if "BASELINE" in p and "ORDER-BEFORE" in p
                  and p["BASELINE"]["final_outcome"] in ("FULL_PASS", "FVBS")
                  and p["ORDER-BEFORE"]["final_outcome"] in ("FULL_PASS", "FVBS")]
        n_base_fvbs = sum(1 for p in usable if p["BASELINE"]["final_outcome"] == "FVBS")
        n_order_fvbs = sum(1 for p in usable if p["ORDER-BEFORE"]["final_outcome"] == "FVBS")
        rate_base = n_base_fvbs / len(usable) if usable else float("nan")
        rate_order = n_order_fvbs / len(usable) if usable else float("nan")

        # discordant: BASELINE FVBS + ORDER FULL_PASS (type A) vs BASELINE FULL_PASS + ORDER FVBS (type B)
        type_a = sum(1 for p in usable if p["BASELINE"]["final_outcome"] == "FVBS" and p["ORDER-BEFORE"]["final_outcome"] == "FULL_PASS")
        type_b = sum(1 for p in usable if p["BASELINE"]["final_outcome"] == "FULL_PASS" and p["ORDER-BEFORE"]["final_outcome"] == "FVBS")
        n_discordant = type_a + type_b

        n_excluded_pairs = len(pairs) - len(usable)
        lines.append(f"  {model}: usable paired trials = {len(usable)}/18 "
                     f"({n_excluded_pairs} pairs excluded -- NOT_IN_SET/struct-fail in at least one condition)")
        lines.append(f"    BASELINE FVBS rate: {n_base_fvbs}/{len(usable)} = {rate_base:.1%} "
                     f"-> ORDER-BEFORE FVBS rate: {n_order_fvbs}/{len(usable)} = {rate_order:.1%} "
                     f"(delta = {(rate_base-rate_order)*100:+.1f}pp)")
        if n_discordant == 0:
            lines.append(f"    McNemar: DEGENERATE, zero discordant pairs (type A={type_a}, type B={type_b}) "
                         f"-- undefined, not a null result.")
        else:
            res = binomtest(type_a, n_discordant, 0.5)
            lines.append(f"    McNemar (exact, via binomtest on discordant pairs): "
                         f"type A(BASELINE=FVBS->ORDER=FULL_PASS)={type_a}, "
                         f"type B(BASELINE=FULL_PASS->ORDER=FVBS)={type_b}, "
                         f"p={res.pvalue:.4f}")
    lines.append("")

    # --- 4. Probe pass rate per model, descriptive ---
    lines.append("PROBE PASS RATE per model, 95% CI (ground truth = Draco alone, weak signal):")
    by_model_probe = defaultdict(list)
    for s in probe_scores:
        model = anon_map[str(s["anon_id"])]["model"]
        by_model_probe[model].append(s)
    for model in MODELS:
        batch = by_model_probe[model]
        n_pass = sum(1 for s in batch if s["score"] == "PROBE_PASS")
        lo, hi = _ci(n_pass, len(batch))
        lines.append(f"  {model}: {n_pass}/{len(batch)} = {n_pass/len(batch):.1%}, CI [{lo:.1f}%,{hi:.1f}%]")

    summary_text = "\n".join(lines)
    db.set_memory("kenji", "sprint14_statistics_summary", summary_text)
    db.set_memory("kenji", "sprint14_statistics_raw", json.dumps(scores, indent=2, ensure_ascii=False))

    print(f"[{NAME}]\n\n{summary_text}")
    print(f"\n\n--- stored as kenji/sprint14_statistics_summary ---")


if __name__ == "__main__":
    run()
