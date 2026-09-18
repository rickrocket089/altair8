"""Sophie's second revision pass on the Sprint 16 synthesis, against
Ingrid's second close-gate verdict (still NEEDS_REVISION, but narrower
and more technical than round 1). Applies exactly her 5 findings.
"""
import os

from dotenv import load_dotenv
from openai import OpenAI

from agents.permissions import require_tool
from agents.team_leader.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "gpt-5.2"


def run() -> None:
    require_tool("team_leader", "read_all")
    db.set_memory("team_leader", "status", "online")

    synthesis = db.get_memory("team_leader", "sprint16_synthesis") or ""
    gate = db.get_memory("ingrid", "sprint16_close_gate") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="team_leader",
        title="Sprint 16 synthesis revision v3: apply Ingrid's second gate findings",
        description="Process Review as hard gate, schema-vs-entry-gate conflict, non-chart exit criterion, schema simplification, Kenji recommendation note.",
    )

    client = OpenAI(api_key=os.environ["TEAM_LEADER_OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model=MODEL, max_completion_tokens=8000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                "Ingrid's second Sprint 16 close-gate verdict is still "
                "NEEDS_REVISION, but narrower -- she confirms the sprint "
                "is 'not close to another elaborate testbed' and the "
                "substance is sound. Apply exactly her 5 findings, "
                "nothing else:\n\n"
                "1. PROCESS REVIEW AS A HARD GATE, not a scheduling note. "
                "State plainly: a Process Review covering Sprints 13-15 "
                "is due (3 sprints since the last review, which covered "
                "10-12) and MUST BE INITIATED -- not merely scheduled -- "
                "before Sprint 17 opens. Ingrid will conduct it. Remove "
                "any language that treats this as a parallel-track to-do.\n\n"
                "2. RESOLVE THE SCHEMA-VS-ENTRY-GATE CONFLICT. The "
                "synthesis pre-resolved the CheckResult schema "
                "(incorporating Mateo's slot-level/composition-rule-level "
                "bifurcation into a specific design) while also listing "
                "Priya/Kenji's pre-build review of that same finding as "
                "a Sprint 17 entry gate -- these conflict. Fix: mark the "
                "CheckResult schema explicitly as PROVISIONAL, subject to "
                "revision by Priya/Kenji's pre-build review, which "
                "remains a real entry gate (not theater). State this "
                "explicitly wherever the schema is described.\n\n"
                "3. ADD A NAMED NON-CHART EXIT CRITERION: at least 2 of "
                "the 3 non-chart contracts (Slider, Carousel, Annotated "
                "Pyramid) must produce a CheckResult with at least one "
                "`not_statically_verifiable` composition-rule finding AND "
                "a populated `communicative_loss` field. State plainly: "
                "if all 3 non-chart contracts instead produce clean, "
                "fully-statically-verified results, that is a suspicious "
                "outcome requiring explanation, not a success -- Sprint "
                "17 does not close green on contract count alone.\n\n"
                "4. SIMPLIFY the composition-rule status field from four "
                "states to three: remove `declared` as a separate status "
                "(redundant -- all rules in a contract are by definition "
                "declared). New states: `statically_verified` / "
                "`statically_violated` / `not_statically_verifiable`.\n\n"
                "5. ADD a note to Sprint 17's researcher brief (for "
                "Kenji): the Minto/Zelazny tagging question should come "
                "with an actual RECOMMENDATION from Kenji, not just the "
                "ambiguity surfaced -- Ingrid's read is that Minto's "
                "Pyramid Principle is clearly rationale-bearing "
                "methodology, not mere prestige attestation, and Kenji "
                "should say so rather than leaving it fully open.\n\n"
                "Output the complete revised deliverable package (all "
                "four parts) with these 5 fixes applied. No preamble, no "
                "changelog -- just the document.\n\n"
                f"=== INGRID'S SECOND CLOSE-GATE REVIEW (full) ===\n{gate}\n\n"
                f"=== CURRENT SYNTHESIS TO REVISE ===\n{synthesis}\n"
            )},
        ],
    )

    revised = response.choices[0].message.content
    if response.choices[0].finish_reason == "length":
        revised += "\n\n[TRUNCATED -- hit max_completion_tokens, incomplete.]"
    db.log_usage("team_leader", response.usage.prompt_tokens, response.usage.completion_tokens)

    db.set_memory("team_leader", "sprint16_synthesis", revised)
    vectorstore.remember(
        collection_name="team_leader_memory",
        doc_id=f"sprint16-synthesis-v3-task-{task_id}",
        text=revised,
        metadata={"agent": "team_leader", "type": "sprint16_synthesis", "version": 3},
    )
    db.update_task(
        task_id, status="completed", result=revised,
        artifact_type="sprint_synthesis",
        artifact_payload={"memory_key": "team_leader/sprint16_synthesis", "version": 3},
    )

    print(f"[{NAME}]\n\n{revised}")
    print(f"\n\n--- v3 stored at team_leader/sprint16_synthesis, {len(revised)} chars ---")


if __name__ == "__main__":
    run()
