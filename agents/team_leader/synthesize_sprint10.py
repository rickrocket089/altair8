"""Sprint 10, Pass 4: Sophie synthesises the three passes into a decision input.

Pass 4 exists because Ingrid found it missing from the original design: Passes
1-3 produce concepts, revisions and verdicts, and none of them produces the
thing this sprint promised the founder -- a comparison he can actually choose
from.

HARD CONSTRAINT, from the design: NO NEW CLAIMS. Pass 4 may only restate,
organise and compare what Passes 1-3 actually produced.

VERIFICATION MECHANISM (Ingrid's New Problem A, agreed as a pre-opening
action): every sentence in the comparison section that has no direct referent
in a Pass 1-3 artifact must be marked [SOPHIE]. Marked sentences are her own
observations, not sprint findings, and are separated in what the founder reads.
Ingrid reviews the marks rather than the whole synthesis, which keeps the check
cheap enough not to become a bottleneck. A synthesis with no marks AND no
direct referents is itself a flag.

Pass 4 has no external check other than this. It is also, per the team's own
history, the step where synthesis has previously drifted from observation into
prescription -- Incident 3 of Process Review #1. The constraint exists because
of that history, not as a formality.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.team_leader.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"


def run() -> None:
    require_tool("team_leader", "read_all")
    db.set_memory("team_leader", "status", "online")

    blind = db.get_memory("priya", "sprint10_concepts_blind") or "(missing)"
    sighted = db.get_memory("priya", "sprint10_concepts_sighted") or "(missing)"
    verification = db.get_memory("kenji", "sprint10_concept_verification") or "(missing)"
    buildability = db.get_memory("mateo", "sprint10_buildability") or "(missing)"

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="team_leader",
        title="Sprint 10 Pass 4: synthesise concepts into a decision input",
        description="Comparative format for the founder. No new claims; Sophie's own observations marked.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Sprint 10, Pass 4. Assemble the sprint's output into the "
            "comparison the founder will choose from.\n\n"
            "THE HARD CONSTRAINT: no new claims. You may restate, organise and "
            "compare what Passes 1-3 produced. You may not add a "
            "characterisation of a concept that none of them made, introduce a "
            "criterion nobody applied, or resolve a disagreement between two "
            "agents by picking one. Where they disagree, show the "
            "disagreement.\n\n"
            "THE MARKING RULE: any sentence you write in the comparison "
            "sections that does not have a direct referent in Pass 1, 2 or 3 "
            "must begin with the marker [SOPHIE]. These are your own "
            "observations. They are allowed and they are wanted -- but they "
            "must be distinguishable from what the sprint found, because you "
            "are the only pass with no external reviewer, and this is the step "
            "where this team's synthesis has drifted from observation into "
            "prescription before. Do not use the marker as decoration on "
            "sentences that do have referents; that would make the mark "
            "meaningless.\n\n"
            "=========== PASS 1 (blind concepts) ===========\n"
            f"{blind}\n\n"
            "=========== PASS 2 (sighted review) ===========\n"
            f"{sighted}\n\n"
            "=========== PASS 3 ROUND 2 (prior-art verification) ===========\n"
            f"{verification}\n\n"
            "=========== MATEO: BUILDABILITY OF THE FALSIFICATION TESTS ===========\n"
            f"{buildability}\n\n"
            "=========== PRODUCE ===========\n\n"
            "SECTION 1 — THE COMPARISON TABLE.\n"
            "One row per concept, all six. Columns: concept name; what it "
            "would build (one line); the generative input it derives form "
            "from; which region of the goal space it serves; Kenji's novelty "
            "verdict and his category (A / B / C); whether the falsification "
            "test is buildable per Mateo; the single biggest named risk. Keep "
            "cells tight -- this is a scanning surface, not prose.\n\n"
            "SECTION 2 — WHERE THE CONCEPTS GENUINELY DIFFER.\n"
            "Plain language. Not a summary of each concept in turn -- an "
            "account of the actual axes of difference between them, so the "
            "founder can see what choosing one over another would commit the "
            "team to. Apply the marking rule here.\n\n"
            "SECTION 3 — WHAT THE SPRINT DID NOT ESTABLISH.\n"
            "State plainly, without softening: which success criteria were met "
            "and which were not; that Kenji placed no concept in Category A; "
            "which novelty claims must be restated before being shown to "
            "anyone; and which concepts rest on prior-art checks this team "
            "cannot currently perform. This section protects the founder from "
            "the table above, which will look more decisive than the evidence "
            "under it.\n\n"
            "SECTION 4 — WHAT A DECISION HERE WOULD ACTUALLY COMMIT TO.\n"
            "For each concept, what building it first would mean for the "
            "team -- drawn from what the passes said, not invented. Apply the "
            "marking rule.\n\n"
            "Do not recommend a winner. The founder chooses, as he has on "
            "every prior direction decision. Your job is to make the choice "
            "legible, not to make it."
        )}],
    ) as stream:
        response = stream.get_final_message()

    synthesis = response.content[0].text
    db.log_usage("team_leader", response.usage.input_tokens, response.usage.output_tokens)

    marks = synthesis.count("[SOPHIE]")
    print(f"[{NAME}] Synthesis written: {len(synthesis)} chars, "
          f"{marks} sentences marked as own observation.")
    if marks == 0:
        print(f"[{NAME}] WARNING: zero marks. Per the agreed mechanism this is "
              f"itself a flag — verify the comparison sections actually have "
              f"referents rather than the marker simply being unused.")

    db.set_memory("team_leader", "sprint10_synthesis", synthesis)
    vectorstore.remember(
        collection_name="team_leader_memory",
        doc_id=f"sprint10-pass4-task-{task_id}",
        text=synthesis,
        metadata={"agent": "team_leader", "type": "sprint_synthesis", "sprint": 10, "pass": 4},
    )
    db.update_task(
        task_id, status="completed", result=synthesis,
        artifact_type="sprint_synthesis",
        artifact_payload={
            "memory_key": "team_leader/sprint10_synthesis",
            "pass": 4,
            "sophie_marks": marks,
        },
    )

    print(f"[{NAME}]\n\n{synthesis}")


if __name__ == "__main__":
    run()
