"""Sophie formally closes Sprint 14: creates the three follow-up backlog
items she specified, marks Backlog #38 resolved, and closes the sprint
via the enforced review gate (log_sprint.py's hard check -- an
'approved' row must already exist in the `reviews` table, produced by
confirm_sprint14_close.py).
"""
from agents.permissions import require_tool
from agents.team_leader.persona import NAME
from tools import db

OUTCOME = (
    "Sprint 14 (Backlog #38) confirms Reading B's core claim: the FVBS "
    "criterion discriminates where F1/F2/F3 could not. Confirmatory FVBS "
    "rate 41/76 = 53.9%, real 95% CI [42.1%,65.5%], landed within the "
    "pre-registered 40-65% band -- models chose the audience-optimal form "
    "on fewer than half of structurally valid trials across 18 main-"
    "analysis scenarios. The mechanism (internalized audience structure "
    "vs. convention-reproduction) remains open -- Hypothesis 6's core "
    "question is narrowed, not closed. NOT-IN-SET (26.7%, above the 5-20% "
    "prediction) disaggregated into 3 verified causes: a real Draco-"
    "vocabulary ceiling (S03/S06/S09/S11/S19), a Draco cost-ranking "
    "exclusion of a valid candidate (S20), and a corrected scorer error "
    "(S14). ORDER-BEFORE McNemar per model returned a real but "
    "underpowered null (5-9 of 18 paired trials excluded per model due "
    "to NOT_IN_SET contamination) -- a different cause than Sprint 13's "
    "degenerate (zero-variance) null. N=3 candidate-set stratum showed an "
    "88% FVBS rate, flagged as a likely small-sample artifact, not a "
    "headline result. Founder's middle-path candidate-set repair (S03/"
    "S14 improved via redesign, S07/S16 remain single-candidate/"
    "exploratory) and infrastructure built this sprint (Registrar rank"
    "ings, matching-rule glossary, FVBS scoring pipeline) are reusable "
    "for future audience-optimality studies."
)

FOLLOWUP_ITEMS = [
    {
        "title": "Sprint 14 NOT-IN-SET — per-scenario disaggregation & candidate-space fix proposals",
        "description": (
            "Build a per-scenario table for Sprint 14's NOT-IN-SET trials (rate + cause: "
            "(a) real Draco/vocabulary gap, (b) Draco cost-ranking exclusion, (c) process/"
            "scorer error) and derive a short list of concrete candidate-space interventions "
            "per cause (e.g. 'extend vocabulary' vs 'raise candidate top-k' vs 'scoring "
            "guardrails'), without rerunning the experiment."
        ),
        "priority": "medium",
    },
    {
        "title": "N=3 stratum anomaly (88% FVBS) — scenario concentration check & robustness check",
        "description": (
            "Check which scenarios/models dominate the N=3 candidate-set stratum, and whether "
            "the 88% FVBS rate is driven by 1-2 scenarios. Produce a robustness check (e.g. "
            "leave-one-scenario-out or a simple sensitivity analysis), clearly marked as "
            "post-hoc/diagnostic, without new data collection."
        ),
        "priority": "low",
    },
    {
        "title": "Hypothesis 6 mechanism test (internalized structure vs. convention-reproduction) — design for causal intervention",
        "description": (
            "Design the next behavioral test that directly discriminates H6's mechanism "
            "(internalized structure vs. convention). Use Sprint 14 findings (audience-optimal "
            "criterion, NOT-IN-SET as a vocabulary-ceiling signal, weak/overlapping probe "
            "results across models) and define: intervention(s), dependent measures, minimal "
            "identification design, and how the 'convention prior' candidate (#11) is "
            "operationalized in a form that makes audience-optimality specifically measurable "
            "(e.g. supply/corruption/order/ablation, but scored against FVBS not F1/F2/F3)."
        ),
        "priority": "high",
    },
]


def run() -> None:
    require_tool("team_leader", "write_backlog")
    db.set_memory("team_leader", "status", "online")

    sprint_id = db.get_sprint_id(14)
    if sprint_id is None:
        raise RuntimeError("Sprint 14 not found -- run confirm_sprint14_close.py first.")

    review = db.get_latest_review(sprint_id)
    if review is None or review["result"] != "approved":
        found = review["result"] if review else "no review found"
        raise RuntimeError(
            f"Sprint 14 cannot be closed: latest review status is '{found}', "
            f"not 'approved'. Run confirm_sprint14_close.py first."
        )

    new_ids = []
    for item in FOLLOWUP_ITEMS:
        item_id = db.create_backlog_item(
            title=item["title"], description=item["description"],
            proposed_by="sophie", priority=item["priority"],
        )
        new_ids.append(item_id)
        print(f"[{NAME}] Backlog #{item_id} created: {item['title']}")

    db.update_backlog_item_status(38, "resolved", resolved_sprint_id=sprint_id)
    print(f"[{NAME}] Backlog #38 marked resolved (resolved_sprint_id={sprint_id}).")

    db.complete_sprint(sprint_id, OUTCOME)
    print(f"[{NAME}] Sprint 14 marked completed.")

    db.set_memory("team_leader", "current_focus",
                  "Sprint 14 closed (Backlog #38, FVBS audience-optimal rerun). "
                  f"3 follow-up backlog items opened (#{new_ids[0]}, #{new_ids[1]}, #{new_ids[2]}). "
                  "Next: sprint planning for one of the follow-ups, per founder's priority call.")

    print(f"\n[{NAME}] Sprint 14 closed. New backlog items: {new_ids}. Backlog #38: resolved.")


if __name__ == "__main__":
    run()
