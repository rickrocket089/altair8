"""Sophie formally closes Sprint 16: creates backlog items for the real
open decisions, logs Process Review #4's structural-action backlog as a
trackable unit (implementation deferred, not lost), and completes the
sprint via the enforced review gate.
"""
from agents.permissions import require_tool
from agents.team_leader.persona import NAME
from tools import db

OUTCOME = (
    "Sprint 16 reconceived Sprint 15's top-ranked concept (FGE) after the "
    "founder's direct critique that inheriting Draco's chart-vocabulary as "
    "the primitive set contradicted Design Principle #4 and the North "
    "Star's browser-substrate position. Result, after 4 rounds of gate "
    "review: Mechanism A (Compositional Rendering Contracts) -- forms "
    "stored as capability-contracts (slots + composition rules) checked "
    "against a declared rendering environment with partial-satisfaction "
    "scoring, ranked by communicative completeness rather than Draco-style "
    "cost. Closest prior-art neighbor: Candidate #4 (NL2INTERFACE/"
    "SmartMLVs); genuine combination-novelty in partial satisfaction + "
    "variable rendering environment + communicative-completeness ranking "
    "together. Real gap closed mid-sprint: neither Minto's Pyramid "
    "Principle nor Zelazny's Say It With Charts had ever been referenced "
    "in this project despite direct relevance -- both distilled (own "
    "words, not copyrighted text) and connected concretely to Mechanism A "
    "(Zelazny's 5 relationship-to-form mappings seed the statistical "
    "contracts' what_it_asserts field; MECE reveals a real gap in the "
    "Annotated Pyramid's composition rule). Mateo's technical consult "
    "found checkability bifurcates into slot-level (mostly solid) vs. "
    "composition-rule-level (often only verifiable at render time, not "
    "declaration time) -- a real architectural refinement carried into "
    "Sprint 17's CheckResult design as provisional pending Priya/Kenji's "
    "entry-gate review. Sprint 17 (not yet opened): Plan A only -- "
    "environment declaration + contract checker + static fixture inputs, "
    "all 8 seed contracts (5 statistical + Slider/Carousel/Annotated "
    "Pyramid), named non-chart exit criterion and comparative CheckResult "
    "table to keep the behavioral-gravity risk (seed set still chart-"
    "heavy) empirically visible rather than just architecturally solved. "
    "Sophie's honest assessment, preserved: Sprint 16 solved the Draco-"
    "vocabulary contradiction; it has not yet solved the risk that "
    "practice stays chart-dominated in behavior. Sprint 15 was also "
    "retroactively closed this session (a real process gap -- it was "
    "never marked completed) and Process Review #4 (Sprints 13-15) was "
    "conducted, finding a flat 40% team self-catch rate and naming 9 "
    "structural actions (S-19 through S-27)."
)

FOLLOWUP_ITEMS = [
    {
        "title": "Minto/Zelazny source-tier tagging: retroactive reclassification scope",
        "description": (
            "Sprint 17 default (if undecided by day 3): tag Minto/Zelazny-derived contract "
            "content as 'structured design knowledge with rationale' (Candidate #2-style), "
            "not source-tier convention attestation. Open question beyond Sprint 17's "
            "immediate need: does this reclassification retroactively apply to other "
            "McKinsey-origin material already treated as convention-prior evidence? "
            "Founder/Sophie decision."
        ),
        "priority": "medium",
    },
    {
        "title": "MECE / vertical-logic as a permanent contract composition-rule category",
        "description": (
            "Kenji's Minto distillation found the Annotated Pyramid contract's composition "
            "rule only covers visual/layout constraints (monotonic rank encoding), not "
            "content/logic constraints (MECE: non-overlapping, collectively exhaustive "
            "groupings). Sprint 17 default: flag the Pyramid contract's CheckResult as "
            "'contract definition incomplete -- pending MECE decision' rather than blocking "
            "on resolution. Design question beyond Sprint 17: should MECE (and possibly "
            "Minto's vertical-logic principle) become a first-class, permanent composition-"
            "rule category across the contract architecture, not just a Pyramid-specific fix?"
        ),
        "priority": "medium",
    },
    {
        "title": "Process Review #4 structural actions (S-19 through S-27): implementation tracking",
        "description": (
            "Process Review #4 (2026-09-18, covering Sprints 13-15) named 9 structural "
            "actions, several explicitly recommended before Sprint 17 opens: S-20 (gate-"
            "script verdict-detection template), S-21 (Deterministic Aggregation Principle "
            "added to Mateo's persona + build checklist), S-22 (concluded-but-unclosed "
            "sprint alert extending the stalled-sprint check), S-23 (practitioner/business "
            "literature as a named scope_checklist.py category + Kenji persona update), "
            "S-24 (acquire/ingest Minto and Zelazny -- see also this item's own backlog "
            "entry once created), S-25 (Kenji synthesis calibration-under-correction "
            "instruction), S-26 (DSR phase tracking -- elevate Backlog #8), S-27 (backlog "
            "staleness audit as a standing process-review agenda item). S-19 (construction-"
            "time correctness criteria) is a standing build-checklist change. None were "
            "implemented as part of Sprint 16's close -- tracked here so they are not lost. "
            "Full text: ingrid/process_review_4."
        ),
        "priority": "high",
    },
]


def run() -> None:
    require_tool("team_leader", "write_backlog")
    db.set_memory("team_leader", "status", "online")

    sprint_id = db.get_sprint_id(16)
    if sprint_id is None:
        raise RuntimeError("Sprint 16 not found.")

    review = db.get_latest_review(sprint_id)
    if review is None or review["result"] != "approved":
        found = review["result"] if review else "no review found"
        raise RuntimeError(
            f"Sprint 16 cannot be closed: latest review status is '{found}', "
            f"not 'approved'."
        )

    new_ids = []
    for item in FOLLOWUP_ITEMS:
        item_id = db.create_backlog_item(
            title=item["title"], description=item["description"],
            proposed_by="sophie", priority=item["priority"],
        )
        new_ids.append(item_id)
        print(f"[{NAME}] Backlog #{item_id} created: {item['title']}")

    db.complete_sprint(sprint_id, OUTCOME)
    print(f"[{NAME}] Sprint 16 marked completed (sprint_id={sprint_id}).")

    db.set_memory("team_leader", "current_focus",
                  "Sprint 15 and 16 both formally closed. Process Review #4 (13-15) "
                  "complete. Sprint 17 NOT yet opened -- founder asked to check in "
                  "before opening it. Pending: 9 Process Review structural actions "
                  f"(backlog #{new_ids[2]}), Minto/Zelazny tagging (#{new_ids[0]}), "
                  f"MECE contract question (#{new_ids[1]}).")

    print(f"\n[{NAME}] Sprint 16 closed. New backlog items: {new_ids}. "
          f"Sprint 17 NOT opened -- awaiting founder check-in.")


if __name__ == "__main__":
    run()
