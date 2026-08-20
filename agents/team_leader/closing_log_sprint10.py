"""Sprint 10 Closing Log + Standing Obligations Check, before the sprint closes.

S7 (Process Review #1): before marking any sprint complete, log new leads,
candidate sprint questions and open threads to the backlog tables, so the
backlog is populated systematically rather than when someone remembers.

Standing Obligations Check (Process Review #2): added after Sprint 8 sat as
in_progress with completed_at NULL, silently skipping both the website update
and the Sprint Review cadence.

Founder chose C1 (The Commitment Audit) as the direction. C2-C6 go to
candidate_approaches so five specified concepts are not lost when the sprint
closes -- that table exists precisely because leads flagged mid-sprint used to
get buried in prose.

Backlog writes are restricted to team_leader, enforced inside tools/db.py
itself rather than at the call site.
"""
from agents.permissions import require_tool
from tools import db

SPRINT_NUMBER = 10

BACKLOG = [
    ("Build the C1 Commitment Audit prototype (founder's Sprint 10 direction)",
     "Founder chose C1 at Sprint 10 close. Agent audits its own claims as evidence / "
     "inference / assumption / assertion with continuous confidence, renders an argument "
     "map where visual weight derives from confidence rather than rhetorical emphasis, "
     "minimum-spanning-argument as the default reading path. Its falsification test is "
     "one of only two Mateo rated runnable in a sprint. Restated novelty claim (naming "
     "PaperTrail and Epistemic Blinding) is at priya/sprint10_restated_claims and must be "
     "used in any external description.", "high"),

    ("Acquire a way to run human-subject studies",
     "Surfaced twice in Sprint 10 from different directions. Three of five falsification "
     "tests are unrunnable purely because they need readers the team cannot recruit, and "
     "Phase C validation of Sprint 9's primitives has now been deferred twice for the same "
     "reason. This is the binding constraint on knowing whether anything the team builds "
     "communicates better. Not a research problem -- a resourcing one.", "high"),

    ("Acquire access to ACM DL / CHI / UIST / InfoVis literature",
     "Two retrieval rounds in Sprint 10 failed to reach the venues where this problem's "
     "prior art actually lives. It blocked verification of C6 entirely, left C2's claim "
     "unresolvable, and Priya self-flagged argument-mapping tools (Rationale, Compendium) "
     "as an unchecked risk to C1. ACM DL was ruled out in Sprint 5 for having no free API; "
     "that decision now has a visible cost. Membership or institutional access would "
     "remove it.", "high"),

    ("Phase C: behavioural validation of Sprint 9's four visual primitives",
     "Still owed. Promised publicly as Sprint 10, deferred at the founder's direction to "
     "design alternatives first, and disclosed as deferred on the live Sprint 9 page. "
     "Blocked by the human-subject capability item above.", "medium"),

    ("Reframe C3 against APT, or retire it",
     "Mackinlay's APT (1986) was retrieved as a primary document and its pipeline is C3's "
     "pipeline. Kenji's proposed recovery: reposition around communication rather than "
     "analysis, since APT's effectiveness criteria are perceptual, not communicative. "
     "Until that argument exists, C3 cannot be shown to anyone.", "medium"),

    ("Close the unreached-literature gaps on C2 and C5",
     "C2: the 1990s-2000s NLG planning literature (Paris, Moore, Reiter and Dale on "
     "user-model-driven generation) was reached only in survey form. C5: the computational "
     "politeness-theory literature (Brown and Levinson in dialogue systems) was not reached "
     "at all. Both bear directly on claims currently carried as unverified.", "medium"),

    ("Fix the non-executable verification instruction in Ingrid's persona",
     "Ingrid's Sprint 10 design review asserted she had cross-checked the process-review "
     "count via tools/db.py. She had not -- reviewer scripts pass her text, not a database "
     "connection. Her conclusion was right; the verification was rhetorical. An instruction "
     "that exceeds an agent's actual capability does not fail loudly, it produces fluent "
     "confabulated compliance. Her own preferred fix: pass real query results into her "
     "review prompts. Every persona instruction of the form 'verify X directly against "
     "source Y' should be audited the same way -- hers is the one that was caught, not "
     "necessarily the only one.", "medium"),

    ("Apply Ingrid's deferred recommendations 8, 9 and 10 from the Sprint 10 design review",
     "Not applied by founder decision, accepted by Ingrid, residual risks recorded: (8) tell "
     "a concept designer the browser is the current medium and to name any ideal-vs-"
     "renderable gap; (9) a self-identification field in prior-art verdicts, as data on how "
     "far pass-blinding held; (10) a positive success criterion in the concept template "
     "(what could a human do that they cannot now), distinct from falsification. Revisit "
     "before the next concept-generation round.", "low"),
]

CANDIDATES = [
    ("C2: Audience-in-the-Loop Simulation", "concept",
     "Agent's audience model made explicit, reader-facing and contestable, structurally prior "
     "to form selection. Prior art: PosterMate, Proxona (2025). Priya declines to claim "
     "novelty -- only that the reader-facing/form-determinative distinction 'is the only thing "
     "that might be novel'. Full spec at priya/sprint10_concepts_blind.", "medium"),
    ("C3: Dimensionality-First Rendering", "concept",
     "Spatial primitives selected by dimensionality analysis, no chart-type taxonomy. "
     "Contradicted by Mackinlay's APT (1986). Needs reframing before reuse -- see the "
     "backlog item.", "low"),
    ("C4: Decision-Surface Rendering", "concept",
     "Artifact geometry derived from the reader's decision; criteria reweighting makes "
     "recommendation robustness visible. Prior art: NL2INTERFACE, MCDM literature. Its own "
     "falsifier is unusually sharp -- higher confidence without higher decision quality means "
     "the concept is actively harmful.", "medium"),
    ("C5: Relational Register Adaptation", "concept",
     "Rhetorical structure derived from a four-axis sender-receiver relational map. Positioned "
     "inside computational register synthesis. Primary failure mode is invisible from inside "
     "the system: a wrong relational map produces an artifact that looks correct.", "medium"),
    ("C6: Diegetic Data Embedding", "concept",
     "Data encoded into a depiction of its own subject rather than displayed beside it. The "
     "one concept Priya did not find blind -- it came from Naledi's Sprint 9 survey. No prior "
     "art found, but that is a retrieval failure, not a finding.", "high"),
]


def run() -> None:
    require_tool("team_leader", "write_backlog")
    db.set_memory("team_leader", "status", "online")
    sprint_id = db.get_sprint_id(SPRINT_NUMBER)

    print("SPRINT CLOSING LOG — Sprint 10")
    print("New leads noted mid-sprint: five unbuilt concepts (C2-C6) -> candidate_approaches")
    print("Candidate sprint questions:   C1 build; two capability gaps; C3 reframe")
    print("Unresolved threads:           Phase C; C2/C5 literature gaps; Ingrid persona fix\n")

    existing = {i["title"] for i in db.list_backlog_items()}
    for title, desc, prio in BACKLOG:
        if title in existing:
            print(f"  = backlog exists: {title[:60]}")
            continue
        db.create_backlog_item(title=title, description=desc,
                               proposed_by="team_leader", priority=prio)
        print(f"  + backlog [{prio}]: {title[:60]}")

    have = {c["title"] for c in db.list_candidate_approaches()}
    for title, cat, desc, prio in CANDIDATES:
        if title in have:
            print(f"  = candidate exists: {title[:60]}")
            continue
        db.create_candidate_approach(
            title=title, description=desc, category=cat,
            source_reference="Sprint 10 Pass 1/2 (priya/sprint10_concepts_blind)",
            flagged_by="priya", sprint_id=sprint_id, priority=prio,
        )
        print(f"  + candidate [{prio}]: {title[:60]}")

    print("\nSTANDING OBLIGATIONS CHECK — Sprint 10")
    print("  [ ] Sprint formally closed via log_sprint.py — NOT YET "
          "(blocked: no approved review row for sprint_id "
          f"{sprint_id}; Ingrid's close review must run first)")
    print("  [ ] Site updated with this sprint's close — NOT YET "
          "(comparison page is live but unlinked; index counter still reads 9)")
    print("  [x] Sprint Review due? NO — Review #2 covered sprints 6-9; #3 due at Sprint 12")
    print("  [x] Backlog entries logged from the Closing Log above — DONE")


if __name__ == "__main__":
    run()
