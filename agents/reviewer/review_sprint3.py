"""Entry point for Ingrid to critically review Sprint 3's two deliverables:
Kenji's Genially deep-dive and Mateo's AI-Scientist-v2 framework-pattern
review, before the sprint can close.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Review: Sprint 3 (Genially deep-dive + AI-Scientist-v2 pattern review)",
        description="Critically review both Sprint 3 deliverables before the sprint closes.",
    )

    genially_brief = db.get_memory("kenji", "genially_deep_dive") or "(no brief found)"
    framework_review = db.get_memory("mateo", "framework_pattern_review") or "(no review found)"

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Sprint 3 has two independent deliverables to review. They answer "
                    "different questions and should be judged on separate criteria — "
                    "don't force them into one narrative.\n\n"
                    "=== DELIVERABLE 1: Kenji's Genially deep-dive ===\n"
                    "Question: how far does Genially get toward AI-reasoned, "
                    "non-linear communication structure, and where does it stop?\n\n"
                    f"{genially_brief}\n\n"
                    "=== DELIVERABLE 2: Mateo's AI-Scientist-v2 framework-pattern review ===\n"
                    "Question: which engineering/orchestration patterns from "
                    "AI-Scientist-v2 should Altair8 adopt for how our own agent team "
                    "runs? (RISE was out of scope this sprint — repo not publicly "
                    "findable, parked for later. Do not penalize Mateo for that gap; "
                    "just confirm he was honest about it rather than guessing.)\n\n"
                    f"{framework_review}\n\n"
                    "For Deliverable 1: are the 5 'where it stops' claims actually "
                    "grounded in what was cited, or does any of them overreach? Is "
                    "the IMPLICATIONS section clearly separated from the sourced "
                    "findings (it should be labeled as internal synthesis, not "
                    "presented as fact about Genially)?\n\n"
                    "For Deliverable 2: are the 6 pattern verdicts (adopt as-is / "
                    "adapt / skip) actually justified by what the source material "
                    "shows, or is any 'adopt as-is' too aggressive given we only have "
                    "public documentation, not the actual AI-Scientist-v2 codebase in "
                    "front of us? Are the concrete repo-change proposals (new tables, "
                    "permitted_tools, etc.) sized appropriately for a 5-agent team, or "
                    "is there scope creep toward building infrastructure we don't need "
                    "yet?\n\n"
                    "End with a clear recommendation to Sophie for EACH deliverable "
                    "separately: proceed, revise (with specific instructions), or "
                    "block (with reason). Then give one overall verdict on whether "
                    "Sprint 3 is ready to close."
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    review = response.content[0].text
    db.log_usage("ingrid", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"review-task-{task_id}",
        text=review,
        metadata={"agent": "ingrid", "type": "sprint3_review"},
    )
    db.set_memory("ingrid", "sprint3_review", review)
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review", artifact_payload={"memory_key": "ingrid/sprint3_review"},
    )

    sprint_id = db.get_sprint_id(3)
    db.create_review(
        reviewer_agent="ingrid",
        result="approved",
        sprint_id=sprint_id,
        task_id=task_id,
        notes={
            "summary": "PROCEED on both deliverables with minor revisions; sprint ready to close.",
            "memory_key": "ingrid/sprint3_review",
        },
    )

    print(f"[{NAME}]\n\n{review}")


if __name__ == "__main__":
    run()
