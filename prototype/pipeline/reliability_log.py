"""Stage 2 reliability logging -- explicitly NOT a Backlog #9 instrument.

Question 1 (what this measures): are LLM-generated Vega-Lite specs
syntactically/structurally valid enough to use in a pipeline without a
correction step? A spec can pass this check and still reflect a
confabulated or inappropriate form choice; it can fail this check for
reasons unrelated to reasoning quality (e.g. a stale field name). This is
an engineering reliability metric.

Question 2 (Backlog #9's actual question -- NOT measured here): did the
model choose the *right* visual representation for the audience and goal?
That requires a different instrument this module does not implement.

Also doubles as the empirical basis for revisiting the Stage 2 model
default in providers.py (currently gpt-5.2, flagged as untested by Ingrid's
review) -- log entries are keyed by generator_model.
"""
import json
import os
from datetime import datetime, timezone

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "workspace", "outputs", "prototype-runs", "stage2_reliability_log.jsonl")


def log_result(slot_id: str, generator_model: str, validation_passed: bool, description: str) -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "slot_id": slot_id,
        "generator_model": generator_model,
        "validation_passed": validation_passed,
        "description": description,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def summarize() -> dict:
    if not os.path.exists(LOG_PATH):
        return {"total": 0}
    entries = []
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    by_model: dict[str, dict[str, int]] = {}
    for e in entries:
        m = e["generator_model"]
        by_model.setdefault(m, {"pass": 0, "fail": 0})
        by_model[m]["pass" if e["validation_passed"] else "fail"] += 1
    return {"total": len(entries), "by_model": by_model}
