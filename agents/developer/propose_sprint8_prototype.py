"""Sprint 8, first task: Mateo studies TVIR's real implementation (not just
the paper) and proposes a scoped first-prototype plan, including a reasoned
position on the target output medium -- the central open question from the
founder's Sprint 7 TVIR read.

TVIR ground truth below was fetched directly by the orchestrating session
from github.com/NJU-LINK/TVIR (README, directory tree, and a real sample
report.md) -- Tier-1 ground truth, same pattern as Sprint 4's direct skill-
file reads, not a paraphrase or a guess.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.developer.persona import NAME, SYSTEM_PROMPT
from agents.permissions import require_tool
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

TVIR_ARCHITECTURE = """
=== TVIR-Agent's 4-stage pipeline (from the real README) ===
Stage 1 -- Research-Grounded Planning: Planner parses the task, invokes search
tools, synthesizes a structured outline with visual requirements attached.
Stage 2 -- Visual Asset Instantiation: an Image Searcher retrieves images via
Google Image Search; a Chart Generator creates data visualizations.
Stage 3 -- Context-Aware Sequential Writing: a Writer generates the report
section by section, interleaving text and visual elements as it goes.
Stage 4 -- Global Index Polishing: a Polisher removes uncited references,
deduplicates, and renumbers figures.

=== Real directory structure (github.com/NJU-LINK/TVIR, Apache 2.0) ===
agent/main.py                      -- entry point
agent/conf/                        -- yaml configs (per-agent, per-LLM-provider)
agent/src/core/orchestrator.py     -- orchestration logic
agent/src/core/pipeline.py         -- the 4-stage pipeline itself
agent/src/io/input_handler.py, output_formatter.py
agent/src/llm/providers/{anthropic,openai}_client.py -- swappable LLM backends
benchmark/                         -- 100-task eval benchmark + per-metric eval scripts
  (eval_chart_quality.py, eval_chart_source_consistency.py,
   eval_figure_caption_quality.py, eval_image_quality.py, etc.)

Requires (from .env.example): SERPER_API_KEY (Google Search), E2B_API_KEY
(sandboxed code execution for chart generation), OPENAI_API_KEY, a VQA model
for image understanding.

=== CRITICAL FINDING: what TVIR's output actually IS ===
Fetched a real sample report (benchmark/reports/claude-4-5/000001/report.md,
583 lines). It is a static Markdown document: headings, paragraphs, inline
citation links (<a href="#ref1">[1]</a>), and images embedded via literal
HTML <figure>/<img>/<figcaption> tags pointing at local PNG/WEBP chart and
image files. There is no interactivity, no dynamic layout, no zoom, nothing
beyond what a rendered Markdown-to-HTML/PDF pipeline produces. TVIR's own
output medium is exactly the "polished paper" the founder was skeptical of
-- confirmed directly from real output, not assumed from the paper's prose.
"""


def run() -> None:
    require_tool("mateo", "write_task_artifact")
    sprint_id = db.get_sprint_id(8)
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="mateo",
        title="Sprint 8: TVIR study + first-prototype proposal",
        description="Real architecture study + reasoned output-medium position + scoped prototype plan.",
    )

    hypotheses = db.get_memory("team_leader", "hypotheses") or ""
    design_principles = db.get_memory("team_leader", "design_principles") or ""

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Sprint 8 is the team's first sprint in DSR's 'Design & "
                    "Development' phase. Backlog #11: resolve the target "
                    "output medium (empirically, through building, not by "
                    "deciding on paper first) and propose Altair8's first "
                    "iterative prototype -- a TVIR-inspired multi-stage "
                    "pipeline, since TVIR is the closest existing analog the "
                    "founder has found. This is a PROPOSAL task, not a "
                    "coding task yet.\n\n"
                    f"REAL TVIR ARCHITECTURE (Tier-1 ground truth, fetched "
                    f"directly from the actual GitHub repo, not the paper's "
                    f"prose):\n{TVIR_ARCHITECTURE}\n\n"
                    f"THE TEAM'S HYPOTHESES:\n{hypotheses}\n\n"
                    f"THE TEAM'S DESIGN PRINCIPLES:\n{design_principles}\n\n"
                    "Produce a proposal with these four parts:\n\n"
                    "1. ARCHITECTURE ASSESSMENT: what should Altair8 reuse "
                    "or directly adapt from TVIR's 4-stage pipeline pattern "
                    "(planning -> visual asset generation -> sequential "
                    "writing -> polishing), and what needs to be built "
                    "fresh because TVIR doesn't address it? Be specific -- "
                    "which stage(s) are content-agnostic orchestration "
                    "patterns worth borrowing, and which are tied to TVIR's "
                    "own report-medium choice and therefore NOT reusable "
                    "as-is for Altair8.\n\n"
                    "2. OUTPUT MEDIUM POSITION: TVIR's actual output is a "
                    "static Markdown report with embedded images -- exactly "
                    "the 'polished paper' format the founder was skeptical "
                    "of. Design principle #4 commits Altair8 to NOT "
                    "constraining output to flat, static formats. Take a "
                    "real position: should Altair8's first prototype target "
                    "a genuinely different output medium (e.g. a rendered, "
                    "interactive HTML page -- not a markdown file), or is "
                    "starting with something report-like still the right "
                    "FIRST step (per the design-principle-#4 addendum: "
                    "implementation ease can pick what ships first, without "
                    "lowering the ultimate ambition)? Don't just restate the "
                    "open question -- make a call, and name what you're "
                    "trading off.\n\n"
                    "3. SCOPED FIRST-PROTOTYPE PLAN: concrete enough that it "
                    "could actually be built next. What does it take as "
                    "input, what does it produce, which stages does it "
                    "implement, which LLM(s) does it use (per design "
                    "principle #2 -- not bound to one model), what's "
                    "explicitly OUT of scope for v1.\n\n"
                    "4. TOOL-USE NOTE: does this first prototype naturally "
                    "involve code execution or tool use (e.g. to render a "
                    "chart, to build an interactive page)? If so, flag that "
                    "backlog #9 (tool-access vs. no-tool-access on "
                    "principled-vs-confabulated reasoning) could be tested "
                    "as a natural byproduct of building this, not a forced "
                    "addition."
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    proposal = response.content[0].text
    db.log_usage("mateo", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="developer_memory",
        doc_id=f"sprint8-prototype-proposal-task-{task_id}",
        text=proposal,
        metadata={"agent": "mateo", "type": "sprint8_prototype_proposal"},
    )
    db.set_memory("mateo", "sprint8_prototype_proposal", proposal)
    db.update_task(
        task_id, status="completed", result=proposal,
        artifact_type="proposal",
        artifact_payload={"memory_key": "mateo/sprint8_prototype_proposal"},
    )

    print(f"[{NAME}] Sprint 8 prototype proposal:\n\n{proposal}")


if __name__ == "__main__":
    run()
