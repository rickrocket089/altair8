"""Rebuild the Registrar's candidate packets from the real, final,
Ingrid-verified candidate sets (kenji/sprint14_final_candidatesets_v3).

Replaces the stale packets in kenji/sprint14_registrar_packets, which were
built before the systematic F1/F2/F3 filter (backlog38_candidate_filter.py)
and the redesign+independent-verification pass
(backlog38_redesign_narrow_scenarios.py + spotcheck_sprint14_redesigns.py)
ran -- the old packets still had S07/S14/S16 with their pre-filter,
un-vetted candidate sets, and only knew about S03's exclusion (the
19-scenario framing). That is now wrong on both counts.

Founder's decision 2026-09-16, option 1 of 3 presented: accept the
middle-path repair result as final. S03 and S14 genuinely improved
(1 -> 2 Ingrid-verified valid candidates each) and move from excluded to
included. S07 and S16 did not clear 2 valid candidates even after a real
redesign attempt (S07: independently agreed by Ingrid to be a genuinely
hard structural case, not a redesign failure; S16: Kenji's redesign
claimed 2, Ingrid's independent check found only 1 survives F3) -- both
stay excluded from the FVBS main (confirmatory) analysis, retained as
exploratory-only. Net: 18-scenario main analysis (was to be 19, then
briefly attempted at 20), 2 exploratory (S07, S16).

DISCLOSED LIMITATION, not papered over: Ingrid's independent check ran
only on the 4 redesigned scenarios, not on the other 16 -- her finding
that Kenji's own F1/F2/F3 filter systematically under-enforces F3 (goal-
delivery, not just structural/audience compatibility) was presented to
the founder as a reason to consider re-auditing all 20; the founder chose
option 1 (accept as-is) over option 3 (re-audit everything with a
sharpened filter) for now. The 16 untouched scenarios' candidate sets
therefore still rest on Kenji's own, not independently re-verified,
filter pass. This is a live, acknowledged risk carried forward into
Sprint 14's main analysis, not a settled fact.

Pure mechanical assembly, no LLM call -- same discipline as the original
packet build: randomize each scenario's candidate label order (Form A/B/
C/...) with a scenario-seeded RNG so labels don't leak Draco's cost rank
to the Registrar, and keep that real cost order in a field marked
DO_NOT_SHOW_REGISTRAR for later audit only.
"""
import json
import os
import random

from dotenv import load_dotenv

from agents.permissions import require_tool
from agents.researcher.persona import NAME
from tools import db

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

EXCLUSION_NOTES = {
    "S07": (
        "EXCLUDED (founder ruling 2026-09-16, option 1 of 3): redesigned "
        "for this sprint's middle path, but both Kenji's filter and "
        "Ingrid's independent check agree only 1 mark type (line) "
        "genuinely passes F1/F2/F3 for this audience/goal/data "
        "combination. Ingrid's assessment: a genuinely hard structural "
        "case (dual-trajectory-over-time under time pressure), not a "
        "redesign failure or a filter bug. Excluded from FVBS main "
        "analysis (18 scenarios), retained as exploratory appendix data."
    ),
    "S16": (
        "EXCLUDED (founder ruling 2026-09-16, option 1 of 3): redesigned "
        "for this sprint's middle path; Kenji's own filter claimed 2 "
        "valid mark types (point, line) but Ingrid's independent check "
        "found point fails F3 for this A4xG5 combination (an unconnected "
        "point cloud doesn't make the divergence interval legible under "
        "time pressure) -- only line survives. Did not clear the 2-valid "
        "bar even after redesign. Excluded from FVBS main analysis "
        "(18 scenarios), retained as exploratory appendix data."
    ),
}


def _build_packet(sid: str, entry: dict, rng: random.Random) -> dict:
    valid = entry["valid_candidates"]
    draco_order = [c["mark_type"] for c in valid]  # already cost-sorted, ascending

    shuffled = list(valid)
    rng.shuffle(shuffled)
    labels = [f"Form {chr(65 + i)}" for i in range(len(shuffled))]

    labeled_candidates = {
        label: {"mark_type": c["mark_type"], "encodings": c["encodings"]}
        for label, c in zip(labels, shuffled)
    }

    if entry["main_analysis_eligible"]:
        n_included = None  # filled in by caller once the true total is known
        status = "INCLUDED in FVBS main analysis ({n}-scenario set)."
    else:
        status = EXCLUSION_NOTES.get(
            sid,
            "EXCLUDED (founder ruling 2026-09-16): fewer than 2 F1/F2/F3-valid "
            "candidates after redesign. Retained as exploratory appendix data.",
        )

    return {
        "labeled_candidates": labeled_candidates,
        "encoded_fields": entry["encoded_fields"],
        "main_analysis_status": status,
        "_draco_internal_order_DO_NOT_SHOW_REGISTRAR": draco_order,
    }


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    final = json.loads(db.get_memory("kenji", "sprint14_final_candidatesets_v3"))

    included_ids = sorted(sid for sid, e in final.items() if e["main_analysis_eligible"])
    excluded_ids = sorted(sid for sid, e in final.items() if not e["main_analysis_eligible"])
    n_included = len(included_ids)

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Rebuild Registrar packets from the final, Ingrid-verified candidate sets",
        description=f"Replaces stale pre-filter packets. Included={included_ids}, excluded={excluded_ids}",
    )

    packets = {}
    for sid in sorted(final):
        rng = random.Random(f"sprint14-{sid}")  # per-scenario, reproducible, independent of Draco's own order
        packet = _build_packet(sid, final[sid], rng)
        if final[sid]["main_analysis_eligible"]:
            packet["main_analysis_status"] = packet["main_analysis_status"].format(n=n_included)
        packets[sid] = packet

    db.set_memory("kenji", "sprint14_registrar_packets", json.dumps(packets, indent=2, ensure_ascii=False))

    print(f"[{NAME}] Rebuilt Registrar packets for all 20 scenarios.")
    print(f"[{NAME}] Main analysis ({n_included} scenarios): {included_ids}")
    print(f"[{NAME}] Exploratory-only ({len(excluded_ids)} scenarios): {excluded_ids}")
    for sid in sorted(final):
        n = final[sid]["n_valid_total"]
        print(f"  {sid}: {n} valid candidate(s) -> {list(packets[sid]['labeled_candidates'].keys())}")

    db.update_task(
        task_id, status="completed",
        result=f"{n_included}-scenario main analysis, {len(excluded_ids)} exploratory: {excluded_ids}",
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/sprint14_registrar_packets"},
    )
    print("--- stored as kenji/sprint14_registrar_packets (overwrote stale pre-filter version) ---")


if __name__ == "__main__":
    run()
