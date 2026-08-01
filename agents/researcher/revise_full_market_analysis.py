"""Entry point for Kenji to revise the Sprint 5 full market analysis per
Ingrid's review. Reads his original brief + Ingrid's critique and produces a
revised version that becomes the new current version (kenji/full_market_analysis).
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))


def run() -> None:
    require_tool("kenji", "write_brief")
    original = db.get_memory("kenji", "full_market_analysis") or ""
    review = db.get_memory("ingrid", "sprint5_review") or ""

    if not original or not review:
        raise RuntimeError("Missing original brief or Ingrid's review — run those first.")

    db.set_memory("kenji", "full_market_analysis_v1", original)

    task_id = db.create_task(
        created_by="ingrid",
        assigned_to="kenji",
        title="Revise Sprint 5 full market analysis per Ingrid's review",
        description="Apply Ingrid's Reason 1 revision instructions.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Your original brief:\n\n{original}\n\n"
                    f"Ingrid's full Sprint 5 review:\n\n{review}\n\n"
                    "Apply her 'Reason 1' revision instructions specifically "
                    "-- this is a targeted text revision, not new research:\n\n"
                    "1. Move the database-failure caveat out of the "
                    "mechanical-pre-check footnote and into the body of "
                    "Category 4 itself. State explicitly there that only "
                    "OpenAlex was operational during this run (arXiv, "
                    "Semantic Scholar, and IEEE Xplore all failed live), so "
                    "IEEE VIS / IEEE TVCG venue coverage came from "
                    "opportunistic web search rather than a systematic IEEE "
                    "Xplore query, and forward-citation analysis on "
                    "LLM4Vis/DracoGPT (which Semantic Scholar would provide) "
                    "was not possible.\n"
                    "2. Downgrade the confidence rating for 'LLM4Vis is the "
                    "closest academic work' from High to Medium, with the "
                    "stated dependency on a future arXiv/Semantic Scholar "
                    "re-run explicitly noted in the confidence table.\n"
                    "3. Sharpen the LLM4Vis/DracoGPT 'closest work found' "
                    "claim: state explicitly that this entire subfield "
                    "(LLM4Vis, DracoGPT, Visualization JUDGE) operates at "
                    "the chart-selection level, one abstraction level below "
                    "Altair8's presentation-level research question -- not "
                    "just as a passing caveat, but as the precise "
                    "characterization of what gap remains.\n"
                    "4. Soften the Peirce paper citation-practice claim from "
                    "'no AI paper in any sprint has cited this' to 'not "
                    "cited in any paper reviewed across Sprints 1-5' (the "
                    "stronger claim isn't verifiable, the weaker one is).\n"
                    "5. Add one explicit sentence flagging that a targeted "
                    "(not full-sprint) re-run of arXiv + Semantic Scholar is "
                    "an open follow-up item once those sources are confirmed "
                    "stable, aimed specifically at forward-citation checks "
                    "on LLM4Vis and DracoGPT.\n\n"
                    "Keep everything else as-is -- the OpenAlex table, the "
                    "open-source framework findings, the Category 1-3 "
                    "self-checks, and the overall structure are all "
                    "confirmed sound by Ingrid. Output the complete revised "
                    "brief."
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    revised = response.content[0].text
    db.log_usage("kenji", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"full-market-analysis-revised-task-{task_id}",
        text=revised,
        metadata={"agent": "kenji", "type": "full_market_analysis_revised"},
    )
    db.set_memory("kenji", "full_market_analysis", revised)
    db.update_task(
        task_id, status="completed",
        result="Revision applied; see kenji/full_market_analysis.",
        artifact_type="research_brief",
        artifact_payload={"memory_key": "kenji/full_market_analysis"},
    )

    print(f"[{NAME}] Revised full market analysis:\n\n{revised}")


if __name__ == "__main__":
    run()
