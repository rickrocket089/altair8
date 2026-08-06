"""Ingrid reviews Mateo's Sprint 8 first-prototype proposal -- the team's
first real architecture decision in DSR's Design & Development phase.
Real content review before any code gets written.
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
        title="Review: Sprint 8 first-prototype proposal",
        description="Mateo's TVIR-study + output-medium decision + scoped v1 plan, before any code is written.",
    )

    proposal = db.get_memory("mateo", "sprint8_prototype_proposal") or "(no proposal found)"
    hypotheses = db.get_memory("team_leader", "hypotheses") or ""
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
                    "This is the team's first real architecture proposal in "
                    "DSR's Design & Development phase -- before this, "
                    "everything was research/analysis. Review it before any "
                    "code gets written, not after.\n\n"
                    f"THE TEAM'S HYPOTHESES:\n{hypotheses}\n\n"
                    f"THE TEAM'S DESIGN PRINCIPLES:\n{design_principles}\n\n"
                    f"MATEO'S PROPOSAL:\n\n{proposal}\n\n"
                    "Specific things to check:\n\n"
                    "1. The output-medium call (interactive HTML over "
                    "Markdown) is justified against design principle #4 and "
                    "its implementation-ease addendum. Does the reasoning "
                    "actually hold, or is 'interactive HTML' itself still a "
                    "fairly conservative choice dressed up as ambitious -- "
                    "i.e. is Mateo making the same kind of quiet settling "
                    "the addendum warns against, just one step further than "
                    "Markdown instead of all the way to what DP #4 actually "
                    "asks for (zoom, motion, multi-dimensional views)?\n\n"
                    "2. Is the 'what's reusable vs. rebuilt' assessment of "
                    "TVIR's 4 stages actually correct, or does it understate "
                    "how much of stages 2 and 3 needs to change? (Mateo says "
                    "stage 3's 'sequential writing discipline' is reusable -- "
                    "check whether that's really independent of the medium, "
                    "or whether writing prose that 'refers to' interactive "
                    "elements is a different enough skill that calling it "
                    "reusable overstates the continuity.)\n\n"
                    "3. Is the v1 scope actually buildable and well-bounded, "
                    "or does it hide complexity? Look specifically at the "
                    "Visual Asset Generator stage -- 'LLM synthesizes chart "
                    "data based on real retrieved figures, or a lightweight "
                    "search call' is vague. Does this undermine the "
                    "'prove the stage works' goal if the data sourcing is "
                    "this loosely specified?\n\n"
                    "4. Does the proposal violate design principle #2 (not "
                    "bound to one model) anywhere in practice, even though "
                    "it claims provider-agnosticism? (E.g. is defaulting "
                    "Claude for planning/writing and GPT for visual specs a "
                    "reasoned choice or an unexamined default?)\n\n"
                    "5. The tool-use note proposes backlog #9 as a natural "
                    "byproduct (log validation failure rate on LLM-generated "
                    "Vega-Lite specs with vs without sandbox validation). Is "
                    "that actually a clean test of principled-vs-"
                    "confabulated reasoning, or does it conflate 'does the "
                    "spec render without errors' (a syntax question) with "
                    "'is the reasoning behind the choice principled' (Sprint "
                    "6/7's actual question)? Be precise about what this "
                    "would and wouldn't tell us.\n\n"
                    "6. Anything scoped OUT that shouldn't be, or anything "
                    "IN that should be cut for a genuine first prototype?\n\n"
                    "End with a recommendation: proceed to build, revise the "
                    "proposal first, or block."
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
        metadata={"agent": "ingrid", "type": "sprint8_prototype_proposal_review"},
    )
    db.set_memory("ingrid", "sprint8_prototype_proposal_review", review)
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review", artifact_payload={"memory_key": "ingrid/sprint8_prototype_proposal_review"},
    )

    print(f"[{NAME}]\n\n{review}")


if __name__ == "__main__":
    run()
