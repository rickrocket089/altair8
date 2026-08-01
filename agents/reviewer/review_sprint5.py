"""Entry point for Ingrid to critically review Sprint 5: Kenji's full market
analysis, explicitly audited against tools/scope_checklist.py's 4 required
categories -- the exact discipline this checklist was built to enforce.
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
        title="Review: Sprint 5 (full market analysis, checklist audit)",
        description="Critically review Kenji's full market analysis before the sprint closes.",
    )

    brief = db.get_memory("kenji", "full_market_analysis") or "(no brief found)"

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Sprint 5 exists specifically because Sprint 2/3 silently "
                    "skipped a required category (foundation-model-native "
                    "capabilities) and nobody on the team caught it -- the "
                    "founder did. Your job this review is explicitly broader "
                    "than usual: not just evidentiary rigor of what's "
                    "submitted, but whether the brief's own self-check "
                    "against the 4 required categories (third-party tools, "
                    "foundation-model-native, open-source frameworks, "
                    "academic research) is honest and complete, per your "
                    "persona's standing instruction to check scope "
                    "completeness against tools/scope_checklist.py.\n\n"
                    f"{brief}\n\n"
                    "Specific things to scrutinize:\n\n"
                    "1. OPERATIONAL RELIABILITY ISSUE: the brief reports that "
                    "3 of 4 literature databases (arXiv, Semantic Scholar, "
                    "IEEE Xplore) failed live with errors during this run -- "
                    "only OpenAlex actually returned data. Kenji handled the "
                    "failure gracefully and was transparent about it, but "
                    "assess: does this materially weaken Category 4's "
                    "'academic research' coverage claim? A category audited "
                    "with 1 of 4 intended sources isn't the same evidentiary "
                    "strength as all 4 -- say so explicitly if the brief "
                    "doesn't already caveat this clearly enough.\n\n"
                    "2. Are the tags 'genuinely new' vs 'confirmatory noise' "
                    "in the OpenAlex paper table actually justified by the "
                    "descriptions given, or does any paper get waved through "
                    "without real scrutiny?\n\n"
                    "3. The claim that LLM4Vis and DracoGPT are 'the closest "
                    "academic work to form-selection reasoning found across "
                    "all 5 sprints' is a strong claim -- is it earned by what "
                    "was actually quoted, or does it overreach the way "
                    "Mateo's Sprint 3/4 claims sometimes did?\n\n"
                    "4. Check the Category-by-category self-check section "
                    "specifically -- is each of the 4 categories addressed "
                    "honestly (including admitting when something is "
                    "confirmatory rather than new), or does the brief pad "
                    "any category to look more complete than it is?\n\n"
                    "5. The mechanical keyword pre-check at the end shows "
                    "all 4 categories as 'mentioned' -- given your own "
                    "persona's warning about this checker (a keyword hit "
                    "does not prove real coverage), verify this against the "
                    "actual content above, not just trust the automated "
                    "flag.\n\n"
                    "End with a recommendation: proceed, revise (with "
                    "specific instructions), or block. Then state plainly "
                    "whether Sprint 5 has genuinely closed the scope gap "
                    "that caused this sprint to exist, or whether the "
                    "literature-database reliability issue means a partial "
                    "re-run is needed once arXiv/Semantic Scholar/IEEE are "
                    "confirmed working again."
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
        metadata={"agent": "ingrid", "type": "sprint5_review"},
    )
    db.set_memory("ingrid", "sprint5_review", review)
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review", artifact_payload={"memory_key": "ingrid/sprint5_review"},
    )

    print(f"[{NAME}]\n\n{review}")


if __name__ == "__main__":
    run()
