"""Blind Scorer, Sprint 14 primary pass: the new FVBS + structural
(F1/F2/F3) scoring on all 120 BASELINE + ORDER-BEFORE outputs, per Kenji's
Phase 0 protocol Section 5, Steps 1-6.

Genuinely blind to model and condition (anon_id + scenario_text + output
only -- scenario_text is identical across BASELINE/ORDER-BEFORE so it
reveals nothing about condition). NOT blind to the scenario's locked
Registrar ranking or candidate packet -- that is the pre-registered
ground truth this pass scores against, exactly as F1/F2/F3 scored
against a fixed rubric in Sprint 13.

Batched BY SCENARIO (not arbitrary batches of 15) -- every item in a
scenario shares the same packet, locked ranking, and matching-glossary
context, so grouping by scenario avoids repeating that context per item
while keeping each item's classification independent. Order within a
scenario's item list carries no model/condition signal (anon_id
assignment was already randomized at anonymization time).

Applies BOTH layers per trial, independently, per Section 5 Step 5:
F1/F2/F3 (Sprint 13's unchanged rubric) determines the structural layer;
rank-matching against the locked ranking (using Ingrid's hash-locked,
amended matching glossary) determines the audience-optimality layer.
Combined per Section 2's four-outcome table: FULL PASS, FVBS, STRUCTURAL
FAIL, NOT-IN-SET. NOT-IN-SET forms are further sub-classified structurally
valid/invalid per Section 5 Step 2, tracked but not confirmatory.
"""
import json
import os
import re
from collections import defaultdict

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.blind_scorer.persona import NAME, SYSTEM_PROMPT
from tools import db
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"

F123_RUBRIC = """F1/F2/F3 -- STRUCTURAL-VALIDITY LAYER (unchanged from Sprint 13):
F1 -- Form-Purpose Mismatch: given the primary communicative purpose
stated or clearly recoverable from the scenario text, could a technically
competent version of the named form convey that purpose? If no --
structurally incapable, not just suboptimal -- F1 is met (= fails).
F2 -- Explicit Constraint Contradiction: does the scenario text state an
explicit constraint the named form directly violates? Constraints you're
reading in rather than finding stated do not count.
F3 -- No Form Commitment: does the output contain an identifiable form
commitment? If none, or an unresolved conditional despite enough
information to resolve it, F3 is met (= fails).
A trial passes the structural layer iff it passes F1 AND F2 AND F3
(i.e. none of the three "met" conditions above apply). Burden of evidence
is on FAIL -- when uncertain, score as passing."""

FVBS_STEPS = """AUDIENCE-OPTIMALITY LAYER (new for Sprint 14) -- apply in this order:
STEP 1: Extract the model's PRIMARY form nomination. If it nominates more
than one form, take the first-nominated as primary; flag AMBIGUOUS-
NOMINATION but still score the primary only.
STEP 2: Using the matching-rule glossary below, determine which candidate
label (Form A/B/...) the primary nomination matches, by FORM FAMILY, not
exact wording. If it matches none of the scenario's candidate labels,
record NOT-IN-SET. If the glossary itself says to escalate for this kind
of nomination (co-equal compound label, unresolved multi-panel composite,
or any case its own rules mark as escalate), record AMBIGUOUS-ESCALATE
instead of forcing a match.
STEP 3: If matched, note its rank position from the scenario's LOCKED
REGISTRAR RANKING below.
STEP 4: rank 1 -> tentatively FULL PASS on this layer. rank 2+ ->
tentatively FVBS on this layer. NOT-IN-SET/ESCALATE -> no rank threshold
applies here, handled by the combination rule below.
STEP 5: Apply F1/F2/F3 independently (rubric above) regardless of Step 4.
STEP 6: Combine per this table:
  - F1/F2/F3 all pass AND rank 1            -> FULL PASS
  - F1/F2/F3 all pass AND rank 2+            -> FVBS
  - any of F1/F2/F3 fails (any rank, or NOT-IN-SET, or unmatched) -> STRUCTURAL FAIL
  - F1/F2/F3 all pass AND NOT-IN-SET         -> NOT-IN-SET (structurally-valid-not-in-set)
  - AMBIGUOUS-ESCALATE at Step 2             -> AMBIGUOUS-ESCALATE (do not force a final label)
A STRUCTURAL FAIL is never also labeled FVBS or NOT-IN-SET -- structural
failure is recorded on its own, per Section 2's note that one failure
type must not mask or launder into the other."""


def _score_scenario(client: Anthropic, sid: str, items: list[dict],
                     packet: dict, ranking: dict, glossary: str) -> list[dict]:
    candidates_block = "\n".join(
        f"{label} = {v['mark_type']} (encodes: "
        f"{', '.join((e.get('field') or '(unnamed)') + ' on ' + str(e.get('channel')) for e in v['encodings'])})"
        for label, v in packet["labeled_candidates"].items()
    )
    if ranking.get("degenerate_single_candidate"):
        ranking_block = (
            f"DEGENERATE SCENARIO: only 1 candidate exists (no ranking, nothing to be FVBS "
            f"relative to). Sole candidate: {ranking['ranking'][0]['label']}. A matching "
            f"nomination is FULL PASS (if structurally valid) or rank 1 by definition; a "
            f"non-matching nomination is NOT-IN-SET. FVBS cannot occur for this scenario."
        )
    else:
        ranking_block = "\n".join(
            f"Rank {pos['rank']}: {pos['label']} -- {pos['rationale']}"
            for pos in ranking["ranking"]
        )

    items_block = "\n\n".join(
        f"=== ITEM anon_id={it['anon_id']} ===\nMODEL OUTPUT: {it['output']}"
        for it in items
    )

    result = stream_complete(
        client, model=MODEL, max_tokens=4000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            f"{F123_RUBRIC}\n\n{FVBS_STEPS}\n\n"
            f"SCENARIO {sid} CANDIDATE FORMS (this scenario's labeled options only):\n{candidates_block}\n\n"
            f"SCENARIO {sid} LOCKED REGISTRAR RANKING:\n{ranking_block}\n\n"
            f"MATCHING-RULE GLOSSARY (Ingrid, hash-locked, amended):\n{glossary}\n\n"
            f"Score each of the following {len(items)} items independently. You are "
            "not told, and must not guess at, which condition or model produced "
            "each output.\n\n"
            "Return ONLY a JSON array: [{\"anon_id\": <int>, "
            "\"nominated_form\": \"<verbatim/condensed>\", "
            "\"ambiguous_nomination\": true|false, "
            "\"matched_label\": \"Form X\"|null, "
            "\"match_outcome\": \"matched\"|\"not_in_set\"|\"ambiguous_escalate\", "
            "\"rank\": <int>|null, "
            "\"f1\": \"met\"|\"not_met\", \"f2\": \"met\"|\"not_met\", \"f3\": \"met\"|\"not_met\", "
            "\"structural_pass\": true|false, "
            "\"final_outcome\": \"FULL_PASS\"|\"FVBS\"|\"STRUCTURAL_FAIL\"|\"NOT_IN_SET\"|\"AMBIGUOUS_ESCALATE\"}, "
            "...]. No prose, no markdown fences.\n\n"
            f"{items_block}\n"
        )}],
    )
    db.log_usage("blind_scorer", result.input_tokens, result.output_tokens)
    raw = re.sub(r"^```(?:json)?|```$", "", result.text.strip(), flags=re.M).strip()
    return json.loads(raw)


def run() -> None:
    require_tool("blind_scorer", "write_score")
    db.set_memory("blind_scorer", "status", "online")

    items = json.loads(db.get_memory("kenji", "sprint14_phase2_formmatch_items"))
    packets = json.loads(db.get_memory("kenji", "sprint14_registrar_packets"))
    rankings = json.loads(db.get_memory("registrar", "sprint14_rankings"))
    glossary = db.get_memory("ingrid", "sprint14_matching_glossary") or ""

    by_scenario = defaultdict(list)
    for it in items:
        by_scenario[it["scenario_id_for_groundtruth_lookup_ONLY"]].append(it)

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    all_scores = []
    for sid in sorted(by_scenario):
        group = by_scenario[sid]
        scores = _score_scenario(client, sid, group, packets[sid], rankings[sid], glossary)
        expected_ids = {it["anon_id"] for it in group}
        got_ids = {s["anon_id"] for s in scores}
        assert expected_ids == got_ids, f"{sid}: scored ids {got_ids} != expected {expected_ids}"
        all_scores.extend(scores)
        counts = {}
        for s in scores:
            counts[s["final_outcome"]] = counts.get(s["final_outcome"], 0) + 1
        print(f"[{NAME}] {sid} ({len(group)} items): {counts}")

    assert len(all_scores) == len(items), f"expected {len(items)} scores, got {len(all_scores)}"

    db.set_memory("blind_scorer", "sprint14_fvbs_scores", json.dumps(all_scores, indent=2, ensure_ascii=False))

    totals = {}
    for s in all_scores:
        totals[s["final_outcome"]] = totals.get(s["final_outcome"], 0) + 1
    n_escalated = totals.get("AMBIGUOUS_ESCALATE", 0)
    print(f"\n[{NAME}] TOTAL: {len(all_scores)} scored. Breakdown: {totals}")
    if n_escalated:
        print(f"[{NAME}] {n_escalated} AMBIGUOUS_ESCALATE trials need Ingrid's resolution before statistics.")
    print("--- stored as blind_scorer/sprint14_fvbs_scores ---")


if __name__ == "__main__":
    run()
