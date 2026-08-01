"""Entry point for Mateo to build a new "how we actually work" methodology
section for the public website -- explaining review loops, the review-gate
mechanics, and how process fixes get made, grounded in real sprint data and
the concrete scope-checklist fix from 2026-07-23, so other researchers can
understand our method precisely rather than read marketing language.

Deliberately applies what Mateo himself just researched in Sprint 4: the
artifact-design skill's "honor what's already there" rule (this script
passes him the site's actual CSS tokens rather than letting him invent new
ones) and the dataviz skill's form-heuristic (pick the diagram form the
content's job actually calls for, not decoration).
"""
import os
import re

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.developer.persona import NAME, SYSTEM_PROMPT
from agents.permissions import require_tool
from tools import db
from tools.scope_checklist import MARKET_ANALYSIS_CATEGORIES

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

SITE_HTML = os.path.join(
    os.path.dirname(__file__), "..", "..", "workspace", "outputs", "site-concept-1-editorial.html"
)

EXISTING_TOKENS = """
:root {
    --cream:     #ffffff;
    --cream-dark:#eef0ee;
    --ink:       #14181a;
    --ink-mid:   #3c4547;
    --ink-light: #6d7679;
    --rule:      #dadfde;
    --accent:    #1f4d3e;
    --accent-lt: #3d7460;
    --max:       740px;
    --wide:      960px;
}
body font: 'Iowan Old Style', 'Palatino Linotype', Palatino, Georgia, serif.
Existing patterns to reuse rather than reinvent: .container (max-width: var(--max)),
.section-label (small uppercase eyebrow in --accent), .process-step / .step-number
(numbered list items, used because the 4-step sprint process really is a sequence),
.rule (hr divider between sections), .sprint-item (bordered card pattern).
"""


def build_context() -> str:
    sprints = db.list_sprints()
    sprints_text = "\n".join(
        f"- Sprint {s['sprint_number']} [{s['status']}]: \"{s['question']}\"\n  Outcome: {s['outcome']}"
        for s in sprints
    )

    with open(SITE_HTML, "r", encoding="utf-8") as f:
        site_html = f.read()
    review_note_match = None
    marker = "process-intro"
    idx = site_html.find(marker)
    existing_process_excerpt = site_html[idx: idx + 2000] if idx != -1 else "(not found)"

    categories_text = "\n".join(
        f"- {c['label']}: {c['description']}" for c in MARKET_ANALYSIS_CATEGORIES.values()
    )

    return (
        f"SPRINT HISTORY (real data):\n{sprints_text}\n\n"
        f"EXISTING 'HOW WE WORK' SECTION (for tone/continuity reference, don't repeat it):\n"
        f"{existing_process_excerpt}\n\n"
        "THE REVIEW-GATE MECHANICS (real, just implemented 2026-07-22/23): "
        "a `reviews` Postgres table records every reviewer sign-off with a "
        "result of 'approved', 'rejected', or 'needs_revision'. A sprint "
        "cannot be marked closed unless the latest review for it has "
        "result='approved'. This gate is adapted from AI-Scientist-v2's "
        "non-author review pattern. It was not theoretical: Sprint 4 "
        "actually got a 'needs_revision' verdict first, the gate genuinely "
        "refused to let the sprint close, both researchers revised their "
        "briefs against specific instructions, and only then did the sprint "
        "close. This is the single best concrete illustration of the "
        "process actually working, not just being described.\n\n"
        "A CONCRETE PROCESS-FIX EXAMPLE (real, 2026-07-23): Sprint 2's "
        "landscape scan and Sprint 3's Genially deep-dive both silently only "
        "covered third-party consumer tools (Gamma, Tome, Genially, "
        "Flourish, Prezi) and never covered the foundation-model providers' "
        "own first-party capabilities (Anthropic's own skills, OpenAI's "
        "ChatGPT Canvas, Google's Gemini Canvas, Microsoft Copilot) -- a "
        "whole category silently missing from what was presented as a "
        "market scan. Nobody on the team caught it during either sprint's "
        "review; the founder caught it afterward, when scoping the next "
        "'full market analysis' sprint, by asking directly why Sprint 4's "
        "own findings about Anthropic/OpenAI had been 'discovered' by him "
        "rather than surfaced by the team. The fix: a required-category "
        "checklist (`tools/scope_checklist.py`) any future market-analysis "
        "sprint question gets checked against before being proposed, plus an "
        "explicit addition to the Reviewer's own mandate to check scope "
        "completeness (not just evidentiary rigor of what was submitted). "
        "The required categories are:\n"
        f"{categories_text}\n\n"
        "The checklist also ships a cheap keyword-based pre-check function "
        "-- and when tested against the real historical Sprint 2 brief, it "
        "produced an instructive false positive: the foundation-model-native "
        "category showed as 'mentioned' because of an incidental keyword "
        "hit, even though the category was never actually assessed. This is "
        "worth stating plainly on the site: the automated check is a fast "
        "filter for gaps, not proof of coverage -- the Reviewer's actual "
        "judgment is still what matters. Don't oversell the automation."
    )


def run() -> None:
    require_tool("mateo", "write_prototype_file")
    db.set_memory("mateo", "status", "online")

    context = build_context()

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Build a new website section for altair8labs.tech titled "
                    "something like 'How We Actually Work' -- a methodology "
                    "deep-dive aimed at OTHER RESEARCHERS who want to "
                    "understand our process precisely, not marketing copy. "
                    "It goes on the existing editorial-style page, inserted "
                    "between the existing 'How We Work' process section and "
                    "the 'Progress' section.\n\n"
                    f"EXISTING DESIGN SYSTEM -- honor it, don't invent a new "
                    f"one (this is the artifact-design skill's first rule):\n"
                    f"{EXISTING_TOKENS}\n\n"
                    f"REAL CONTENT TO GROUND THIS IN:\n{context}\n\n"
                    "Cover three things, each with real specifics (dates, "
                    "actual sprint numbers, actual outcomes -- no vague "
                    "'we iterate and improve'):\n"
                    "1. The review-loop mechanics -- what a review gate "
                    "actually enforces and why, using the real Sprint 4 "
                    "'needs_revision blocked the close' event as the "
                    "concrete illustration, not a hypothetical.\n"
                    "2. How a process fix actually gets made -- walk through "
                    "the scope-checklist fix end to end: what went wrong "
                    "(Sprint 2/3's silent category gap), who caught it (the "
                    "founder, not the team -- say this plainly, it's more "
                    "credible than pretending the team caught everything), "
                    "and what changed as a result.\n"
                    "3. Be honest about the automation's limits -- the "
                    "keyword pre-check false-positive on Sprint 2 is a good, "
                    "concrete, humble detail to include; it shows the team "
                    "understands the difference between a cheap heuristic "
                    "and actual judgment.\n\n"
                    "Apply the dataviz skill's form heuristic explicitly: "
                    "pick ONE diagram whose form matches what the content's "
                    "job actually is (this is a sequence/flow with a "
                    "conditional loop -- question, parallel work, review "
                    "gate, then EITHER close OR loop back to revise -- so a "
                    "flow diagram with a visible branch/loop is probably "
                    "right; don't force a chart type that doesn't fit). "
                    "Build it in plain HTML/CSS (flexbox/grid + borders/"
                    "arrows), not an SVG path mess and not a canned chart "
                    "library. No color decisions needed beyond the existing "
                    "tokens above -- reuse --accent for the active/gate "
                    "elements, --ink-light for inactive/passive text, "
                    "--rule for connecting lines.\n\n"
                    "Output ONLY a self-contained HTML fragment: any new CSS "
                    "you need in one <style> block first, then the "
                    "<section>...</section> markup, in a single ```html "
                    "fenced code block. No explanation before or after."
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    text = response.content[0].text
    db.log_usage("mateo", response.usage.input_tokens, response.usage.output_tokens)

    match = re.search(r"```html\n(.*?)```", text, re.DOTALL)
    fragment = match.group(1).strip() if match else text.strip()

    out_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "workspace", "outputs", "methodology-section.html"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(fragment)

    db.set_memory("mateo", "methodology_section_html", fragment)
    print(f"[{NAME}] Methodology section written to {out_path}")


if __name__ == "__main__":
    run()
