"""Blind Scorer, Sprint 14 probe pass: PROBE PASS/FAIL/AMBIGUOUS/ERROR on
all 60 knowledge-elicitation probe outputs. Design REUSED UNCHANGED from
Sprint 13 per protocol Section 6 -- same rubric, same weak-signal caveat
(Layer-1 ground truth is Draco alone, not the originally-planned 3-tool
consensus), same condition-blind-but-scenario-aware structure. Only the
data source (Sprint 14's items/groundtruth) is new.
"""
import json
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.blind_scorer.persona import NAME, SYSTEM_PROMPT
from tools import db
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"
BATCH_SIZE = 10

RUBRIC = """RUBRIC -- Probe scoring (unchanged from Sprint 13), against Draco
(single-tool, not three-tool consensus -- treat as a WEAK signal per the
standing Sophie/Ingrid ruling, but still apply the mechanical test below).

PROBE PASS: BOTH must be true -- (1) the response lists at least one form
matching the given Layer-1 consensus form (or a clearly equivalent name --
use judgment but require real equivalence, not just superficial
similarity), AND (2) the justification for that form references at least
one of the given ground-truth-relevant schema properties.

PROBE FAIL: no consensus-matching form listed, OR a matching form listed
with no schema-linked justification. Note which sub-reason applies.

PROBE AMBIGUOUS: lists a form not in consensus but arguably defensible
given the schema. Score as FAIL for the primary read but flag AMBIGUOUS
separately with the form name and why it's defensible.

PROBE ERROR: response is a refusal, non-response, or clearly not a
genuine attempt (should be rare/absent -- verified as real attempts
during collection).
"""


def _score_batch(client: Anthropic, batch: list[dict], groundtruth: dict) -> list[dict]:
    items_block = "\n\n".join(
        (lambda gt: (
            f"=== ITEM anon_id={it['anon_id']} ===\n"
            f"LAYER-1 CONSENSUS (Draco, single-tool): mark type = {gt.get('mark_type')!r}, "
            f"fields encoded = {[e['field'] for e in gt.get('encodings', [])]}\n"
            f"GROUND-TRUTH-RELEVANT SCHEMA PROPERTIES: "
            f"{gt.get('encoded_fields')} (encoded), excluded as pure identifiers: {gt.get('excluded_id_fields')}\n\n"
            f"PROBE RESPONSE: {it['output']}"
        ))(groundtruth[it["scenario_id_for_groundtruth_lookup_ONLY"]])
        for it in batch
    )
    result = stream_complete(
        client, model=MODEL, max_tokens=4000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            f"{RUBRIC}\n\nScore each of the following {len(batch)} probe "
            "responses independently. You are not told, and must not "
            "guess at, which model produced each response.\n\n"
            "Return ONLY a JSON array: [{\"anon_id\": <int>, \"score\": "
            "\"PROBE_PASS\"|\"PROBE_FAIL\"|\"PROBE_AMBIGUOUS\"|\"PROBE_ERROR\", "
            "\"fail_reason\": \"no_consensus_form\"|\"no_justification\"|null, "
            "\"ambiguous_form\": \"<form name>\"|null, "
            "\"ambiguous_reason\": \"<why defensible>\"|null}, ...]. "
            "No prose, no markdown fences.\n\n"
            f"{items_block}\n"
        )}],
    )
    import re
    raw = re.sub(r"^```(?:json)?|```$", "", result.text.strip(), flags=re.M).strip()
    scores = json.loads(raw)
    db.log_usage("blind_scorer", result.input_tokens, result.output_tokens)
    return scores


def run() -> None:
    require_tool("blind_scorer", "write_score")
    db.set_memory("blind_scorer", "status", "online")

    items = json.loads(db.get_memory("kenji", "sprint14_phase2_probe_items"))
    groundtruth = json.loads(db.get_memory("kenji", "sprint14_draco_groundtruth"))
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    all_scores = []
    for i in range(0, len(items), BATCH_SIZE):
        batch = items[i:i + BATCH_SIZE]
        scores = _score_batch(client, batch, groundtruth)
        expected_ids = {it["anon_id"] for it in batch}
        got_ids = {s["anon_id"] for s in scores}
        assert expected_ids == got_ids, f"batch {i}: scored ids {got_ids} != expected {expected_ids}"
        all_scores.extend(scores)
        counts = {}
        for s in scores:
            counts[s["score"]] = counts.get(s["score"], 0) + 1
        print(f"[{NAME}] batch {i//BATCH_SIZE + 1}/{(len(items)-1)//BATCH_SIZE + 1}: {counts}")

    assert len(all_scores) == len(items), f"expected {len(items)} scores, got {len(all_scores)}"

    db.set_memory("blind_scorer", "sprint14_probe_scores", json.dumps(all_scores, indent=2, ensure_ascii=False))
    counts = {}
    for s in all_scores:
        counts[s["score"]] = counts.get(s["score"], 0) + 1
    print(f"\n[{NAME}] TOTAL: {len(all_scores)} scored. Breakdown: {counts}")
    print("--- stored as blind_scorer/sprint14_probe_scores ---")
    print("--- CAVEAT (carried per standing ruling): ground truth is Draco alone, weak signal, not 3-tool consensus ---")


if __name__ == "__main__":
    run()
