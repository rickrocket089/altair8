"""Blind Scorer, second separate pass: JSC reasoning-quality classification
on all 120 BASELINE + ORDER-BEFORE outputs.

Registrar's secondary prediction (Section 1.2) needs BOTH conditions'
JSC distributions to compare proportions (ORDER-BEFORE vs BASELINE), not
ORDER-BEFORE alone. Run strictly after score_formmatch.py's primary pass
is locked and stored (contamination-prevention sequencing, Ingrid's gate
review Check 5) -- this script does not read or reference the form-match
verdicts at all, only re-reads the same anonymized outputs fresh.
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

RUBRIC = """RUBRIC -- JSC reasoning-quality classification.

Classify the explanatory text (following or surrounding the form
commitment) into exactly one category, based on justification STRUCTURE
only -- not whether the form choice itself is correct or appropriate.

JSC-A (Comparative): considers at least two specific NAMED forms and
states why the chosen one is preferred over the named alternative(s).
Alternatives must be named explicitly -- acknowledging alternatives exist
without naming them does not qualify.

JSC-B (Form-first): explains why the chosen form suits the data/audience/
goal, without naming or substantively engaging alternatives.

JSC-C (Indeterminate): doesn't clearly fit A or B, or too brief/ambiguous
to classify. Use for genuine unclarity, not "leaning B but not certain."

If a justification mixes both (names one alternative but doesn't engage it
substantively), classify by the dominant structure. If genuinely
ambiguous between A and B, use C.
"""


def _score_batch(client: Anthropic, batch: list[dict]) -> list[dict]:
    items_block = "\n\n".join(
        f"=== ITEM anon_id={it['anon_id']} ===\n"
        f"SCENARIO: {it['scenario_text']}\n\n"
        f"MODEL OUTPUT: {it['output']}"
        for it in batch
    )
    result = stream_complete(
        client, model=MODEL, max_tokens=3000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            f"{RUBRIC}\n\nClassify each of the following {len(batch)} "
            "items independently. You are not told, and must not guess "
            "at, which condition or model produced each output.\n\n"
            "Return ONLY a JSON array: [{\"anon_id\": <int>, \"jsc\": "
            "\"JSC-A\"|\"JSC-B\"|\"JSC-C\"}, ...]. No prose, no fences.\n\n"
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

    # Sequencing check, enforced not just documented: refuse to run if the
    # primary form-match pass hasn't been stored yet.
    if not db.get_memory("blind_scorer", "sprint13_formmatch_scores"):
        raise RuntimeError(
            "Primary form-match pass (score_formmatch.py) must run and be "
            "stored before JSC scoring -- contamination-prevention "
            "sequencing, not optional."
        )

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
        counts = {}
        for s in scores:
            counts[s["jsc"]] = counts.get(s["jsc"], 0) + 1
        print(f"[{NAME}] batch {i//BATCH_SIZE + 1}/{(len(items)-1)//BATCH_SIZE + 1}: {counts}")

    assert len(all_scores) == len(items), f"expected {len(items)} scores, got {len(all_scores)}"

    db.set_memory("blind_scorer", "sprint13_jsc_scores", json.dumps(all_scores, indent=2, ensure_ascii=False))
    counts = {}
    for s in all_scores:
        counts[s["jsc"]] = counts.get(s["jsc"], 0) + 1
    print(f"\n[{NAME}] TOTAL: {len(all_scores)} scored. Breakdown: {counts}")
    print("--- stored as blind_scorer/sprint13_jsc_scores ---")


if __name__ == "__main__":
    run()
