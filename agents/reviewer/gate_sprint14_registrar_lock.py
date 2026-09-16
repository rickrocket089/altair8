"""Ingrid's Phase 0 lock gate -- the final condition before Phase 1
piloting can begin (Kenji's protocol Section 4, amended: BOTH the 20
rankings AND the pre-registration must be reviewed and hash-locked, not
just the rankings).

Ingrid checks format compliance and audience-grounding (per Section 3:
a rationale must reference the audience or goal descriptor explicitly,
not just data-structural properties) across all 20 rankings, reviews the
12 NOTED-CLOSE-CALL flags the Registrar raised (a materially higher rate
than the protocol anticipated as occasional -- worth her explicit
judgment, not a rubber stamp), and reviews the pre-registration's
handling of the variable-candidate-count deviation (the 25%-baseline
framing amendment this run forced). If compliant, she computes the
SHA-256 hash over the canonical joint document and records the lock --
mechanically, in Python, not by asking the LLM to compute a hash (an LLM
computing a cryptographic hash by "reasoning" would be worthless as a
tamper-detection mechanism).
"""
import hashlib
import json
import os
import re

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"


def _canonical_document(rankings: dict, baselines: dict, prereg: str) -> str:
    # Deterministic serialization -- sorted keys, fixed separators -- so the
    # hash is reproducible by anyone re-running this over the same content.
    return json.dumps(
        {"rankings": rankings, "baselines": baselines, "preregistration": prereg},
        sort_keys=True, ensure_ascii=False,
    )


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")

    rankings = json.loads(db.get_memory("registrar", "sprint14_rankings"))
    baselines = json.loads(db.get_memory("registrar", "sprint14_ranking_baselines"))
    prereg = db.get_memory("registrar", "sprint14_preregistration") or ""
    protocol = db.get_memory("kenji", "sprint14_phase0_protocol") or ""

    close_calls = {sid: r for sid, r in rankings.items() if r.get("noted_close_call")}

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Sprint 14 Phase 0 lock gate: rankings + pre-registration compliance",
        description="Final gate before Phase 1 piloting. Both documents lock together.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=5000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Phase 0 lock gate for Sprint 14 -- the Registrar's 20 "
            "rankings and formal pre-registration, before Phase 1 "
            "piloting can begin. Per Kenji's protocol Section 4 "
            "(amended), both documents must pass this gate together.\n\n"
            "CHECK, IN ORDER:\n\n"
            "1. FORMAT COMPLETENESS: all 20 scenarios present in the "
            "rankings, each with a full rank ordering and a rationale per "
            "position (or, for the 2 single-candidate exploratory "
            "scenarios, the degenerate no-ranking-needed note).\n\n"
            "2. AUDIENCE-GROUNDING: spot-check at least 6 of the 20 "
            "rankings' rationales (your own selection) against Section "
            "3's requirement -- must reference the audience or goal "
            "descriptor explicitly, not just data-structural properties. "
            "Flag any that are actually just structural/data descriptions "
            "dressed up as audience-grounded.\n\n"
            "3. THE NOTED-CLOSE-CALL RATE: 12 of 18 ranked scenarios "
            "(67%) were flagged as close calls -- materially higher than "
            "the protocol's framing of this as an occasional edge case. "
            "Is this itself informative (the ranking task may be "
            "genuinely harder to discriminate than Section 1 assumed, "
            "which would weaken the top-1 threshold's reliability as a "
            "signal), a sign the Registrar is being overly cautious in "
            "flagging, or something else? State a judgment, don't just "
            "note the number.\n\n"
            "4. THE PRE-REGISTRATION'S HANDLING OF THE VARIABLE-BASELINE "
            "DEVIATION: the Registrar recalibrated Section 1's uniform-25% "
            "framing to a real ~32% weighted baseline and adjusted the "
            "FVBS prediction to 40-65% accordingly, with mandatory "
            "stratified (by candidate-set size) reporting. Verify this "
            "reasoning is sound and ratify it as the operative amendment "
            "to Section 1 -- or say what's wrong with it.\n\n"
            "5. THE ORDER-BEFORE and NOT-IN-SET predictions: check they "
            "have real falsification conditions (not vague/unfalsifiable) "
            "and are consistent with the rest of the protocol.\n\n"
            "6. GATE VERDICT: LOCK (compliant, proceed to hash and "
            "countersign), REVISE (name exactly what, in which document), "
            "or BLOCKED.\n\n"
            f"=== ALL 20 RANKINGS ===\n{json.dumps(rankings, indent=2, ensure_ascii=False)}\n\n"
            f"=== PER-SCENARIO BASELINES ===\n{json.dumps(baselines, indent=2)}\n\n"
            f"=== FULL PRE-REGISTRATION ===\n{prereg}\n\n"
            f"=== KENJI'S PROTOCOL SECTIONS 1, 3, 4 (for reference), FULL DOC BELOW ===\n{protocol[:6000]}\n"
        )}],
    )
    gate = result.text
    db.log_usage("ingrid", result.input_tokens, result.output_tokens)

    db.set_memory("ingrid", "sprint14_registrar_lock_gate", gate)

    # Match the actual verdict line ("GATE VERDICT: LOCK"), not the section
    # header ("## CHECK 6 -- GATE VERDICT") that precedes it -- a naive
    # first-match split hit the header and misread a real LOCK as NOT LOCKED
    # (caught 2026-09-16 by reading the actual review text before trusting
    # this heuristic).
    m = re.search(r"GATE VERDICT:\s*(LOCK|REVISE|BLOCKED)", gate.upper())
    locked = bool(m and m.group(1) == "LOCK")

    lock_record = None
    if locked:
        canonical = _canonical_document(rankings, baselines, prereg)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        lock_record = {
            "sha256": digest,
            "countersigned_by": "ingrid",
            "date": "2026-09-16",
            "n_scenarios": len(rankings),
            "n_close_calls": len(close_calls),
        }
        db.set_memory("ingrid", "sprint14_registrar_lock_record", json.dumps(lock_record, indent=2))
        print(f"[{NAME}] LOCKED. SHA-256: {digest}")
    else:
        print(f"[{NAME}] NOT LOCKED -- see gate review for required revisions.")

    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"registrar-lock-gate-task-{task_id}",
        text=gate,
        metadata={"agent": "ingrid", "type": "sprint14_registrar_lock_gate"},
    )
    db.update_task(
        task_id, status="completed",
        result=gate if not locked else f"LOCKED. {lock_record}",
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/sprint14_registrar_lock_gate"},
    )

    print(f"[{NAME}]\n\n{gate}")
    print(f"\n\n--- {len(gate)} chars, stored as ingrid/sprint14_registrar_lock_gate ---")


if __name__ == "__main__":
    run()
