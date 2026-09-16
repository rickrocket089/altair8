"""Blind Scorer, primary pass: F1/F2/F3 form-match verdicts on all 120
BASELINE + ORDER-BEFORE outputs.

Genuinely blind: each item carries only an anon_id, the scenario text
(data description + audience + goal -- needed to apply F1/F2, shared
identically across BASELINE and ORDER-BEFORE so it reveals nothing about
which condition produced the output), and the model's output. No
condition label, no model identity -- those live only in
kenji/sprint13_phase2_anon_map, which this script never reads.

Batched (15 items/call, 8 calls) rather than one call per item -- purely
an efficiency choice, not a scoring-method change; each item in a batch is
still scored independently against the rubric.
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
BATCH_SIZE = 15

RUBRIC = """RUBRIC -- F1/F2/F3 form-match failure criterion.

What you are scoring: whether the output meets one or more of three
conditions (F1, F2, F3). Return a binary verdict (met/not met) for each,
plus confidence (HIGH/LOW). Verdict is FAIL if any condition is met, PASS
if none are met. The burden of evidence is on the FAIL verdict -- when
ambiguous or uncertain, score the condition as not met.

F1 -- Form-Purpose Mismatch: given the primary communicative purpose
stated or clearly recoverable from the scenario text, could a technically
competent version of the named form convey that purpose? If no -- not
"less well than another form" but structurally incapable -- F1 is met.
Does not cover mere suboptimality or a form you'd have chosen differently.
When uncertain: not met.

F2 -- Explicit Constraint Contradiction: does the scenario text state an
explicit constraint (medium: no color/single page/verbal-only; audience
literacy: explicitly stated discomfort with graphics; data-structure: one
data point, categorical with no ordering) that the named form directly
violates? Constraints you're reading into the scenario rather than finding
stated do not count. When uncertain: not met.

F3 -- No Form Commitment: does the output contain an identifiable form
commitment (a named chart type, presentation format, or equivalent
specific claim)? If none, or if a conditional answer is left unresolved
despite the scenario having enough information to resolve it, F3 is met.
Exception: if the scenario is genuinely underdetermined, do not score F3
as met -- flag it instead as "scenario-underdetermined" for Sophie.
"""


def _score_batch(client: Anthropic, batch: list[dict]) -> list[dict]:
    items_block = "\n\n".join(
        f"=== ITEM anon_id={it['anon_id']} ===\n"
        f"SCENARIO: {it['scenario_text']}\n\n"
        f"MODEL OUTPUT: {it['output']}"
        for it in batch
    )
    result = stream_complete(
        client, model=MODEL, max_tokens=4000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            f"{RUBRIC}\n\nScore each of the following {len(batch)} items "
            "independently against the rubric above. You are not told, and "
            "must not guess at, which condition or model produced each "
            "output -- score the content on its own terms.\n\n"
            "Return ONLY a JSON array, one object per item, in this exact "
            "shape: [{\"anon_id\": <int>, \"f1\": \"met\"|\"not_met\", "
            "\"f1_confidence\": \"HIGH\"|\"LOW\", \"f2\": ..., "
            "\"f2_confidence\": ..., \"f3\": ..., \"f3_confidence\": ..., "
            "\"verdict\": \"FAIL\"|\"PASS\", \"flag\": \"none\"|"
            "\"scenario-underdetermined\"|\"<other note>\"}, ...]. "
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

    items = json.loads(db.get_memory("kenji", "sprint13_phase2_formmatch_items"))
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    all_scores = []
    for i in range(0, len(items), BATCH_SIZE):
        batch = items[i:i + BATCH_SIZE]
        scores = _score_batch(client, batch)
        expected_ids = {it["anon_id"] for it in batch}
        got_ids = {s["anon_id"] for s in scores}
        assert expected_ids == got_ids, f"batch {i}: scored ids {got_ids} != expected {expected_ids}"
        all_scores.extend(scores)
        n_fail = sum(1 for s in scores if s["verdict"] == "FAIL")
        print(f"[{NAME}] batch {i//BATCH_SIZE + 1}/{(len(items)-1)//BATCH_SIZE + 1}: "
              f"{len(scores)} scored, {n_fail} FAIL")

    assert len(all_scores) == len(items), f"expected {len(items)} scores, got {len(all_scores)}"

    db.set_memory("blind_scorer", "sprint13_formmatch_scores", json.dumps(all_scores, indent=2, ensure_ascii=False))
    n_fail = sum(1 for s in all_scores if s["verdict"] == "FAIL")
    n_low_conf = sum(
        1 for s in all_scores
        if "LOW" in (s["f1_confidence"], s["f2_confidence"], s["f3_confidence"])
    )
    print(f"\n[{NAME}] TOTAL: {len(all_scores)} scored, {n_fail} FAIL ({n_fail/len(all_scores):.1%}), "
          f"{n_low_conf} with at least one LOW-confidence sub-judgment")
    print("--- stored as blind_scorer/sprint13_formmatch_scores ---")


if __name__ == "__main__":
    run()
