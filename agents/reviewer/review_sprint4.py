"""Entry point for Ingrid to critically review Sprint 4's two deliverables:
Kenji's foundation-model capability scan and Mateo's skill-mechanism
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
        title="Review: Sprint 4 (foundation-model capability scan + skill mechanism review)",
        description="Critically review both Sprint 4 deliverables before the sprint closes.",
    )

    capability_scan = db.get_memory("kenji", "foundation_model_capabilities_scan") or "(no brief found)"
    mechanism_review = db.get_memory("mateo", "skill_mechanism_review") or "(no review found)"

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Sprint 4 has two independent deliverables. They answer "
                    "different questions and should be judged on separate "
                    "criteria — don't force them into one narrative.\n\n"
                    "=== DELIVERABLE 1: Kenji's foundation-model capability scan ===\n"
                    "Question: have foundation-model providers (Anthropic, "
                    "OpenAI, Google, Microsoft) already solved Altair8's core "
                    "problem -- reasoning about why a visual form communicates "
                    "better -- via their own first-party capabilities? Kenji "
                    "had TIER 1 ground truth (Anthropic's actual artifact-design "
                    "and dataviz skill text, passed to him directly, not web "
                    "search) and TIER 2 web-searched material for the other "
                    "three providers.\n\n"
                    f"{capability_scan}\n\n"
                    "=== DELIVERABLE 2: Mateo's skill-mechanism review ===\n"
                    "Question: how do these providers technically implement "
                    "skill/capability selection and loading, and which "
                    "mechanisms should Altair8 adopt? Same Tier 1/Tier 2 "
                    "evidence split. Deliberately decoupled from Deliverable "
                    "1 -- Mateo was told to ignore content/research questions "
                    "entirely.\n\n"
                    f"{mechanism_review}\n\n"
                    "For Deliverable 1: is the Tier 1 vs Tier 2 confidence "
                    "distinction actually honored throughout, or does "
                    "Tier 2 marketing language (e.g. Google/Microsoft press "
                    "material using the word 'reasoning') get smuggled in as "
                    "if it were equivalent evidence to the directly-observed "
                    "Anthropic material? Is the central claim -- that the "
                    "dataviz skill's form heuristic is 'the closest thing to "
                    "real reasoning found so far, but scoped to charts only' "
                    "-- actually supported by what's quoted, or does it "
                    "overreach in either direction (overselling dataviz's "
                    "generality, or underselling what a Tier-2 competitor "
                    "might actually do)?\n\n"
                    "For Deliverable 2: are the 10 pattern verdicts justified "
                    "by the material shown? In particular scrutinize P3 "
                    "(executable validators) and P4 (deferred loading), which "
                    "Mateo calls the two most important new findings -- do "
                    "the quotes actually support 'adopt as-is' / 'adopt "
                    "adapted', or is Mateo again claiming more architectural "
                    "certainty than public documentation can support (a "
                    "pattern you flagged in his Sprint 3 review)? Is the "
                    "priority order (P3 -> P2 -> P4 -> P8) well-reasoned or "
                    "does it show the same scope-creep tendency you flagged "
                    "last sprint?\n\n"
                    "End with a recommendation to Sophie for EACH deliverable "
                    "separately: proceed, revise (with specific instructions), "
                    "or block. Then give one overall verdict on whether "
                    "Sprint 4 is ready to close, and whether Altair8's "
                    "research question (does a solution already exist) is "
                    "now adequately answered or needs further investigation."
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
        metadata={"agent": "ingrid", "type": "sprint4_review"},
    )
    db.set_memory("ingrid", "sprint4_review", review)
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review", artifact_payload={"memory_key": "ingrid/sprint4_review"},
    )

    print(f"[{NAME}]\n\n{review}")


if __name__ == "__main__":
    run()
