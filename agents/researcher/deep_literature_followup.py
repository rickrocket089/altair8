"""Entry point for Kenji's follow-up to Sprint 5 (Postgres task 35), expanded
per founder feedback: not just re-running arXiv + Semantic Scholar now that
they're confirmed stable, but fixing a real methodological weakness noticed
in the prior runs -- every prior search capped max_results at 5-6 per query,
meaning the literature review never screened a wide pool and filtered down;
it only ever retrieved a narrow top-N and analyzed all of it. This run
widens both result depth (30 per query) and query variety.

Also applies the founder's precision correction from the same conversation:
the actual research question is *why* LLMs currently under-represent
business communication (summaries, visualization choice, chart choice, other
elements) and *what a solution might look like* -- not an assumption that
"reasoning" is necessarily the missing piece. Framed accordingly below.
"""
import os
import time

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, papers, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"
TOOLS = [{"type": "web_search_20260209", "name": "web_search"}]
MAX_RESULTS_PER_QUERY = 30

QUERIES = [
    "LLM4Vis visualization recommendation explanation",
    "DracoGPT visualization design preferences language models",
    "LLM chart type selection reasoning explanation",
    "why LLMs struggle business communication summarization visualization",
    "semantic relationship text visual form generation reasoning",
]


def _extract_text(content) -> str:
    return "\n".join(block.text for block in content if block.type == "text")


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")
    task_id = db.create_task(
        created_by="ingrid",
        assigned_to="kenji",
        title="Deep literature follow-up: wider arXiv/Semantic Scholar sweep + LLM4Vis/DracoGPT citation check",
        description=(
            "Follow-up to Sprint 5 task 35, expanded: fix the shallow "
            "max_results=5-6 retrieval depth from Sprints 1 and 5, and check "
            "for LLM4Vis/DracoGPT successors now that arXiv and Semantic "
            "Scholar are confirmed stable."
        ),
    )

    all_results = []
    per_query_counts = {}
    for query in QUERIES:
        try:
            arxiv_hits = papers.search_arxiv(query, max_results=MAX_RESULTS_PER_QUERY)
        except Exception as e:
            print(f"[papers] arxiv query '{query}' failed, skipping: {e}")
            arxiv_hits = []
        time.sleep(2)  # respect Semantic Scholar's tight per-second rate limit
        try:
            s2_hits = papers.search_semantic_scholar(query, max_results=MAX_RESULTS_PER_QUERY)
        except Exception as e:
            print(f"[papers] semantic_scholar query '{query}' failed, skipping: {e}")
            s2_hits = []
        time.sleep(2)
        per_query_counts[query] = {"arxiv": len(arxiv_hits), "semantic_scholar": len(s2_hits)}
        all_results.extend(arxiv_hits)
        all_results.extend(s2_hits)

    # De-duplicate by (source, external_id) before saving/reporting
    seen = set()
    deduped = []
    for p in all_results:
        key = (p["source"], p["external_id"])
        if key not in seen:
            seen.add(key)
            deduped.append(p)
            papers.save_paper(p)

    by_source: dict[str, list[dict]] = {}
    for p in deduped:
        by_source.setdefault(p["source"], []).append(p)

    lit_summary_lines = [f"Total unique papers retrieved this run: {len(deduped)}"]
    for query, counts in per_query_counts.items():
        lit_summary_lines.append(f"- Query '{query}': arXiv={counts['arxiv']}, Semantic Scholar={counts['semantic_scholar']}")
    lit_summary_lines.append("")
    for source, plist in by_source.items():
        lit_summary_lines.append(f"\n=== {source} ({len(plist)} unique results) ===")
        for p in plist:
            lit_summary_lines.append(f"- {p['title']}\n  {(p['abstract'] or '(no abstract)')[:400]}")
    lit_summary = "\n".join(lit_summary_lines)

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    user_message = {
        "role": "user",
        "content": (
            "This is a follow-up to Sprint 5 (Postgres task 35), expanded "
            "per founder feedback after reviewing our own methodology: "
            "Sprints 1 and 5 both capped max_results at 5-6 per query, "
            "which is not a genuine literature screen -- it's a narrow "
            "top-N retrieval with no filtering step, dressed up as if it "
            "were representative. This run fixes that: 30 results per "
            "query, 5 distinct query framings, across arXiv and Semantic "
            "Scholar (now confirmed stable).\n\n"
            "IMPORTANT FRAMING CORRECTION (apply throughout): the actual "
            "research question is *why LLMs currently under-represent "
            "business communication* -- summaries, choice of visualization, "
            "choice of charts where needed, and possibly other elements -- "
            "and *what a solution might look like*. Do NOT assume "
            "'reasoning about form-selection' is necessarily the missing "
            "piece -- that was our diagnostic lens for scanning the "
            "landscape, not a proven necessary condition for a solution. "
            "The solution space remains genuinely open between at least two "
            "structurally different directions: (a) additional reasoning "
            "that establishes a semantic/logical relationship between "
            "content and visual form, working within existing visualization "
            "primitives, or (b) an entirely new visualization language for "
            "agents that enables possibilities beyond static two-dimensional "
            "slides (motion, 3D, interactive forms), possibly outside the "
            "slide paradigm entirely. Frame findings as evidence relevant to "
            "either direction, not as confirmation that direction (a) is "
            "correct.\n\n"
            f"TIER 1 -- REAL DATA, ALREADY RETRIEVED (live calls, not "
            f"simulated):\n{lit_summary}\n\n"
            "Specific tasks:\n"
            "1. Check specifically for LLM4Vis (Wang et al., EMNLP 2023) and "
            "DracoGPT (Yang et al., IEEE TVCG 2024) successors or extensions "
            "in this wider result set -- this was the specific open item "
            "from Sprint 5's review (Ingrid required this before Category 4 "
            "could be treated as fully closed).\n"
            "2. With 5x-6x the retrieval depth and 5 query framings instead "
            "of 1, assess honestly: does wider search change any Sprint "
            "1/5 conclusion, or does it mostly return the same or "
            "confirmatory material? Say so plainly either way.\n"
            "3. Given the corrected framing above, flag anything -- even "
            "tangential -- relevant to direction (b), the new-visualization-"
            "language possibility, since Sprints 1-5 searched almost "
            "exclusively through a reasoning-shaped lens and may have "
            "under-indexed work relevant to novel visualization media/"
            "languages (e.g. generative graphics, agent-driven interactive "
            "media, non-slide presentation formats).\n"
            "4. Update the confidence rating on the Sprint 5 finding that "
            "'LLM4Vis is the closest work found' given this wider search -- "
            "does it hold at Medium, improve, or need further downgrade?\n\n"
            "End with a clear statement of whether Postgres task 35 (the "
            "open item from Sprint 5) is now resolved."
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

    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"deep-literature-followup-task-{task_id}",
        text=report,
        metadata={"agent": "kenji", "type": "deep_literature_followup"},
    )
    db.set_memory("kenji", "deep_literature_followup", report)
    db.update_task(
        task_id, status="completed", result=report,
        artifact_type="research_brief", artifact_payload={"memory_key": "kenji/deep_literature_followup"},
    )

    print(f"[{NAME}] Deep literature follow-up complete.\n\n{report}")


if __name__ == "__main__":
    run()
