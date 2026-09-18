"""Sophie formally closes Sprint 15 -- a real process gap being fixed
retroactively (caught during Sprint 16's own close gate, 2026-09-17):
Sprint 15's concepts (ACFR, FGE, AAEB, CCO) were produced, reality-
checked, and reviewed, and its outcome was acted on (the founder chose
FGE, which became Sprint 16's starting point) -- but the sprint was
never marked completed in Postgres, which is why Process Review cadence
tracking went stale and Ingrid's Sprint 16 close gate caught it.
"""
from agents.permissions import require_tool
from agents.team_leader.persona import NAME
from tools import db

OUTCOME = (
    "Sprint 15 (Knowledge Layer Concepts, #11-first) delivered 4 genuinely "
    "distinct concepts for a visualization-knowledge layer -- ACFR "
    "(Audience-Conditional Form Register), FGE (Form Grammar Extension), "
    "AAEB (Audience-Annotated Exemplar Bank), CCO (Communicative Claim "
    "Ontology) -- each with a real mechanism, a stated value-add, a "
    "falsifier, and honestly-disclosed risks. Kenji's reality check "
    "grounded each against confirmed prior retrieval (no manufactured "
    "novelty); Ingrid's review confirmed genuine diversity, checked "
    "honest failure-mode disclosure, and flagged DP2/DP4 compliance "
    "concerns (CCO's claim-identification step is the most model-"
    "capability-dependent). Priya's own stated confidence: bet on FGE, "
    "bet against CCO. The founder selected FGE -- but immediately "
    "critiqued its premise (inheriting Draco's chart-vocabulary "
    "contradicts Design Principle #4 and the North Star's browser-"
    "substrate position), which became Sprint 16's actual starting "
    "question rather than a straight build of Sprint 15's FGE as "
    "originally specified. Concepts-only scope was honored -- no "
    "prototype was built in Sprint 15, per the founder's explicit "
    "scoping decision."
)


def run() -> None:
    require_tool("team_leader", "write_backlog")
    db.set_memory("team_leader", "status", "online")

    sprint_id = db.get_sprint_id(15)
    if sprint_id is None:
        raise RuntimeError("Sprint 15 not found -- run confirm_sprint15_close.py first.")

    review = db.get_latest_review(sprint_id)
    if review is None or review["result"] != "approved":
        found = review["result"] if review else "no review found"
        raise RuntimeError(
            f"Sprint 15 cannot be closed: latest review status is '{found}', "
            f"not 'approved'. Run confirm_sprint15_close.py first."
        )

    db.complete_sprint(sprint_id, OUTCOME)
    print(f"[{NAME}] Sprint 15 marked completed (sprint_id={sprint_id}).")


if __name__ == "__main__":
    run()
