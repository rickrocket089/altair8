"""Entry point for Kenji's Sprint 5: the full market analysis the founder
asked for as a starting point before further work, this time explicitly
checked against tools/scope_checklist.py's 4 required categories -- the
exact gap-finding exercise that caused this checklist to exist in the first
place (Sprint 2/3 silently only covered third-party tools).

Two genuinely new pieces of ground this sprint covers that prior sprints
didn't:
1. Academic literature searched across ALL FOUR databases (arXiv, Semantic
   Scholar, OpenAlex, IEEE Xplore) via search_all_sources() -- Sprint 1 only
   ever used arXiv alone.
2. Open-source frameworks beyond AI-Scientist-v2 -- RISE (bhanneke) was
   never actually found/assessed in Sprint 3 and is still an open gap.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, papers, vectorstore
from tools.scope_checklist import MARKET_ANALYSIS_CATEGORIES, format_coverage_report

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

SPRINT_QUESTION = (
    "Full market analysis, checked against all 4 required categories: who "
    "has already solved -- or come closest to solving -- reasoning about "
    "why a visual form communicates better? Fill the remaining gaps from "
    "Sprints 1-4 (broad literature search across all 4 databases, "
    "open-source frameworks beyond RISE)."
)

CORE_RESEARCH_QUERY = (
    "visual communication reasoning audience cognitive load form selection"
)

MODEL = "claude-sonnet-4-6"
TOOLS = [{"type": "web_search_20260209", "name": "web_search"}]


def _extract_text(content) -> str:
    return "\n".join(block.text for block in content if block.type == "text")


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 5: full market analysis (checklist-driven)",
        description=SPRINT_QUESTION,
    )

    # --- Step 1: real literature search across all 4 databases ---
    lit_results = papers.search_all_sources(CORE_RESEARCH_QUERY, max_results_per_source=6)
    for paper in lit_results:
        papers.save_paper(paper)

    by_source: dict[str, list[dict]] = {}
    for p in lit_results:
        by_source.setdefault(p["source"], []).append(p)

    lit_summary_lines = []
    for source, plist in by_source.items():
        lit_summary_lines.append(f"\n=== {source} ({len(plist)} results) ===")
        for p in plist:
            lit_summary_lines.append(f"- {p['title']}\n  {(p['abstract'] or '(no abstract)')[:400]}")
    lit_summary = "\n".join(lit_summary_lines) if lit_summary_lines else "(no results retrieved)"

    # --- Step 2: prior sprint context, so Kenji doesn't repeat known ground ---
    prior_context = (
        "PRIOR SPRINT FINDINGS (do not repeat -- build on/fill gaps in these):\n"
        f"- Sprint 1: arXiv-only literature search on LLM spatial/visual reasoning failure modes.\n"
        f"- Sprint 2: 20-tool landscape scan of third-party AI slide/viz tools "
        f"(Gamma, Tome, Genially, Flourish, Prezi) -- production automated, no communication reasoning found.\n"
        f"- Sprint 3: Genially deep-dive (closest third-party analog, stops at author-scripted "
        f"navigation, no 'why this form' reasoning) + AI-Scientist-v2 pattern review (RISE blocked -- "
        f"repo not publicly findable, still an open gap).\n"
        f"- Sprint 4: Foundation-model-native capabilities (Anthropic's dataviz skill has the closest "
        f"'form heuristic' found anywhere so far, but scoped to charts only, no audience model). "
        f"Ingrid flagged: this only checked *documented* capabilities, not whether base models have "
        f"internalized equivalent reasoning through training -- a separate open question.\n"
    )

    checklist_text = "\n".join(
        f"- {c['label']}: {c['description']}" for c in MARKET_ANALYSIS_CATEGORIES.values()
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    user_message = {
        "role": "user",
        "content": (
            f"Sprint question: {SPRINT_QUESTION}\n\n"
            f"{prior_context}\n\n"
            "REQUIRED CATEGORY CHECKLIST -- this sprint exists specifically "
            "because Sprint 2/3 silently skipped one of these categories and "
            "nobody on the team caught it. You must explicitly address each "
            "one, even to say 'already covered in Sprint N, no new ground "
            "found':\n"
            f"{checklist_text}\n\n"
            "TIER 1 -- REAL DATA, ALREADY RETRIEVED (this is not a web-search "
            "guess -- these are actual results from a live call to "
            f"search_all_sources() across all 4 literature databases, query "
            f"'{CORE_RESEARCH_QUERY}'):\n"
            f"{lit_summary}\n\n"
            "Analyze this literature honestly: does anything here move "
            "beyond what Sprint 1's arXiv-only search and Sprint 4's "
            "capability scan already established? Flag genuinely new "
            "findings vs. confirmatory noise. Note which of the 4 databases "
            "contributed anything Sprint 1 (arXiv-only) would have missed.\n\n"
            "TIER 2 -- WEB SEARCH REQUIRED: search specifically for "
            "open-source frameworks in this space beyond AI-Scientist-v2 -- "
            "the RISE gap from Sprint 3 is still open (repo never found). "
            "Look for: automated visualization-reasoning frameworks, "
            "open-source presentation-generation research projects, any "
            "academic or hobbyist project attempting principled visual-form "
            "selection. Be honest if nothing further is found -- don't "
            "manufacture a finding to fill the category.\n\n"
            "End with an explicit self-check: for EACH of the 4 required "
            "categories, state whether this sprint found anything new, "
            "confirmed prior findings, or genuinely came up empty (and if "
            "empty, say so plainly rather than padding). This self-check is "
            "the actual deliverable Ingrid will audit against the checklist."
        ),
    }
    messages = [user_message]

    response = client.messages.create(
        model=MODEL, max_tokens=8000, system=SYSTEM_PROMPT, tools=TOOLS, messages=messages
    )
    total_input = response.usage.input_tokens
    total_output = response.usage.output_tokens

    while response.stop_reason == "pause_turn":
        messages = [user_message, {"role": "assistant", "content": response.content}]
        response = client.messages.create(
            model=MODEL, max_tokens=8000, system=SYSTEM_PROMPT, tools=TOOLS, messages=messages
        )
        total_input += response.usage.input_tokens
        total_output += response.usage.output_tokens

    report = _extract_text(response.content)
    db.log_usage("kenji", total_input, total_output)

    # Append the mechanical keyword pre-check for Ingrid's convenience (not a
    # substitute for her judgment, but a fast cross-check on Kenji's own claims).
    report_with_precheck = report + "\n\n---\n\n## Mechanical Pre-Check (for Ingrid)\n\n" + format_coverage_report(report)

    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"full-market-analysis-task-{task_id}",
        text=report_with_precheck,
        metadata={"agent": "kenji", "type": "full_market_analysis"},
    )
    db.set_memory("kenji", "full_market_analysis", report_with_precheck)
    db.update_task(
        task_id, status="completed", result=report_with_precheck,
        artifact_type="research_brief", artifact_payload={"memory_key": "kenji/full_market_analysis"},
    )

    print(f"[{NAME}] Full market analysis complete.\n\n{report_with_precheck}")


if __name__ == "__main__":
    run()
