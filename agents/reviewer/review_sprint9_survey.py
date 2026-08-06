"""Ingrid reviews Naledi's Sprint 9 Phase A survey of novel visual-
communication patterns, before Phase B (Mateo) selects candidates to build.
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
        title="Review: Sprint 9 Phase A survey",
        description="Real content review of Naledi's novel-visual-primitives survey before Phase B build decisions.",
    )

    survey = db.get_memory("naledi", "novel_visual_primitives_survey") or "(no survey found)"
    design_principles = db.get_memory("team_leader", "design_principles") or ""

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Naledi surveyed 5 adjacent fields for visual-"
                    "communication patterns outside the standard business-"
                    "chart taxonomy, without web search access (she flags "
                    "this herself and tiers every pattern by confidence -- "
                    "check whether that self-grading is actually accurate, "
                    "not just present).\n\n"
                    f"DESIGN PRINCIPLES:\n{design_principles}\n\n"
                    f"FULL SURVEY:\n\n{survey}\n\n"
                    "Specific things to check:\n\n"
                    "1. Are the confidence tiers (🟢/🟡/🔴) actually applied "
                    "consistently, or does anything marked high-confidence "
                    "look more speculative than that, or vice versa?\n\n"
                    "2. Naledi's Phase B recommendations (scrollytelling, "
                    "annotation-led reading path, force-directed graphs, "
                    "diegetic information display) -- are these genuinely "
                    "the strongest candidates against her own stated "
                    "criteria (real audience/goal gap; buildable without "
                    "special infrastructure; categorically different from "
                    "existing charts, not just styling), or does the "
                    "selection favor patterns that sound impressive over "
                    "ones that actually score best on the criteria?\n\n"
                    "3. Scrutinize 'diegetic information display' "
                    "specifically -- it's the most ambitious pick. Is "
                    "'embed data into a depiction of the entities "
                    "themselves' actually buildable as a v1 prototype, or "
                    "does Naledi's own text ('the agent needs to generate a "
                    "world model of the subject matter... a hard generation "
                    "problem') mean this should be flagged as higher-risk "
                    "than the other three picks, not listed alongside them "
                    "as equally ready?\n\n"
                    "4. Is the portability/infrastructure assessment "
                    "trustworthy, or does 'high portability' sometimes mean "
                    "'a mature JS library exists' while glossing over how "
                    "hard it would be for an LLM agent (not a human "
                    "developer) to correctly generate content for that "
                    "library?\n\n"
                    "5. Naledi's meta-finding -- that the real innovations "
                    "across all 5 fields are about the reader-artifact "
                    "relationship (pacing, positioning, disclosure "
                    "triggers) rather than new chart shapes -- is this "
                    "actually supported by the specific patterns she found, "
                    "or is it an appealing generalization that overreaches "
                    "what 11 patterns from an unverified survey can "
                    "support?\n\n"
                    "6. Does anything here quietly violate a design "
                    "principle while appearing to serve one (e.g. does any "
                    "recommended pattern risk becoming decorative rather "
                    "than communicative, which would undercut DP#1 -- "
                    "result quality first)?\n\n"
                    "End with a recommendation: which patterns (if any) "
                    "Mateo should actually build for Phase B, and whether "
                    "any need Kenji's verification pass before Phase B "
                    "commits build effort."
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
        metadata={"agent": "ingrid", "type": "sprint9_survey_review"},
    )
    db.set_memory("ingrid", "sprint9_survey_review", review)
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review", artifact_payload={"memory_key": "ingrid/sprint9_survey_review"},
    )

    print(f"[{NAME}]\n\n{review}")


if __name__ == "__main__":
    run()
