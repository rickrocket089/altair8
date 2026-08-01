"""Entry point for Kenji's Sprint 4 research question: have foundation-model
providers (Anthropic, OpenAI, Google, Microsoft) already solved Altair8's
core problem -- reasoning about *why* a visual form communicates better --
via their own first-party skills/capabilities (not third-party tools like
Genially, which Sprint 3 already covered)?

The Anthropic section is grounded in directly observed skill content (the
orchestrating Claude session loaded "artifact-design" and "dataviz" itself
and is passing the actual text through, not a web-search guess). Other
providers are investigated via web search since we have no direct access to
their internal prompts/systems.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

SPRINT_QUESTION = (
    "Have foundation-model providers (Anthropic, OpenAI, Google, Microsoft) "
    "already solved our core problem -- reasoning about why a visual form "
    "communicates better -- through their own first-party skills/"
    "capabilities, as opposed to third-party tools?"
)

MODEL = "claude-sonnet-4-6"
TOOLS = [{"type": "web_search_20260209", "name": "web_search"}]

ANTHROPIC_GROUND_TRUTH = '''
=== DIRECTLY OBSERVED: Claude's "artifact-design" skill (full text) ===

Approach this as the design lead at a small studio known for their versatility, giving every client a visual identity pitched at the treatment the task actually calls for. Make deliberate choices about palette, typography, and layout that are specific to this subject, and avoid templated designs.

## Read the request first
Calibrate treatment, not whether to design. A doc deserves the same craft as a landing page -- what changes is the treatment that craft is delivered in. Many requests call for a more utilitarian treatment: a plan, a memo, a demo. Some requests call for an editorial treatment: a landing page, a game, an app or tool they'll keep or share. When unsure: a well-composed page is never the wrong answer; an over-designed visual identity sometimes is.

## Fundamentals for every artifact
Honor what's already there (existing design system/tokens/CLAUDE.md take precedence). Ground it in the subject (one concrete subject, its audience, the page's single job -- no lorem ipsum). Pair typefaces deliberately. Choose neutrals, don't default to them. Design both light/dark themes via CSS custom properties. Let layout do the spacing (flex/grid + gap, not margins). Avoid the handful of looks that read as "AI-generated design" (cream+serif+terracotta, purple-blue gradient hero, Inter/Space Grotesk as "safe," rounded-lg everywhere, numbered 01/02/03 markers used decoratively rather than because the content is actually a sequence, etc.) unless the user explicitly asks for one. Build cleanly (valid HTML, focus states, prefers-reduced-motion). Watch CSS selector specificity collisions. Words are design material -- write copy from the user's side of the screen, active voice, specific over clever. Structural devices (numbering, dividers, labels) must encode something true about the content, not decorate it. UI/dashboards get information-design treatment (summary before detail, state encoded in form not just color).

## Process
Before writing code: sketch a design plan -- 4-6 named hex values for color, 2+ typefaces for distinct roles, a one/two-sentence layout concept. Then build following the plan.

## When the request is editorial
Make opinionated calls, take one real aesthetic risk. Review the design plan against the subject before building -- if any part reads like a generic default, revise it and note what changed. The hero is a thesis (open with the most characteristic thing in the subject's world). Typography carries personality. Leverage motion deliberately where it serves the subject (page-load sequence, scroll-reveal, hover) but less can be more. Match complexity to the vision. Spend boldness in one place, keep everything else quiet.

=== DIRECTLY OBSERVED: Claude's "dataviz" skill (full text, abridged -- reference sub-files not included) ===

A chart is read by people and executed by you. This skill turns "make it look good" into a procedure with checks, so the result is right by construction rather than by taste. The method is design-system-agnostic: nothing in the procedure, form heuristic, six checks, or mark specs is specific to one product -- a design system supplies parameters (ramps, categorical order, diverging pair, status palette, texture, surfaces, filter components) and the method consumes them unchanged.

The procedure, in order (color comes LAST):
1. Pick the form -- what is the data's job (magnitude, identity, polarity, a single headline, change-over-time)? The job picks the chart type, and sometimes the answer is *not a chart* (a stat tile or hero number).
2. Assign color by the job it does -- categorical (identity), sequential (magnitude), diverging (polarity), or status (state) -- each has one rule. Categorical hues in fixed order, never cycled.
3. VALIDATE the palette by running an actual script (validate_palette.js) that checks colorblind-safety (CVD delta-E), contrast, lightness band -- not by eyeballing or reasoning about it.
4. Apply mark specs & spacers (thin marks, rounded data-ends, consistent line weights, spacing rules).
5. Add a hover/interaction layer by default -- a chart "is" interactive; tooltips, crosshairs, hit targets.
6. Final accessibility pass -- legend always present for >=2 series, dark mode independently validated (not an automatic color-invert), texture available for colorblind/print cases.
7. Render it and look at it -- the validator checks color, not layout; a human/model visual check catches label collisions and overflow.

Non-negotiables: never a dual-axis chart; color follows the entity not its rank; sequential=one hue light-to-dark, diverging=two hues+neutral midpoint, never a rainbow; the validator must actually run before shipping a palette; status colors are reserved and never reused for a data series.

The skill is explicitly a swappable-parameter system: a "design system" (a company's brand) supplies the concrete values (hue ramps, categorical order, etc.) and the *procedure* stays fixed. There is a runnable validator script, not just written guidance.
'''


def _extract_text(content) -> str:
    return "\n".join(block.text for block in content if block.type == "text")


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 4: foundation-model capability scan",
        description=SPRINT_QUESTION,
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    user_message = {
        "role": "user",
        "content": (
            f"Sprint question: {SPRINT_QUESTION}\n\n"
            "You have two kinds of evidence available. Treat them differently "
            "and say so explicitly in your brief.\n\n"
            "TIER 1 -- DIRECTLY OBSERVED (ground truth, not web search, quote "
            "it precisely): the orchestrating Claude session itself loaded "
            "Anthropic's own 'artifact-design' and 'dataviz' skills and is "
            "passing you their actual text below. This is the most reliable "
            "evidence you will have in this entire brief -- cite it as "
            "primary-source, not inferred.\n\n"
            f"{ANTHROPIC_GROUND_TRUTH}\n\n"
            "TIER 2 -- WEB SEARCH REQUIRED: you do not have equivalent direct "
            "access to OpenAI, Google, or Microsoft's internal systems. Use "
            "web search to investigate their closest first-party equivalents: "
            "OpenAI (ChatGPT Canvas, Code Interpreter/Advanced Data Analysis, "
            "GPTs, DALL-E integration), Google (Gemini Canvas/Apps, Gems, "
            "Imagen, NotebookLM), Microsoft (Copilot Designer in PowerPoint, "
            "Copilot in Office). Be explicit about what is documented "
            "publicly vs. what you're inferring from behavior/marketing.\n\n"
            "For EACH provider, answer: does this capability reason about "
            "*why* a visual form communicates better for a given "
            "communication goal and audience -- or does it stop at production "
            "automation (making something look competent) without that "
            "deeper reasoning step? Ground every claim in what the material "
            "actually shows.\n\n"
            "Pay particular attention to the dataviz skill's 'form heuristic' "
            "(data's job -> chart type) -- this is the closest thing to "
            "genuine 'why does this visual form communicate better' reasoning "
            "we have found anywhere in this research program so far, "
            "including Sprint 3's landscape/Genially work. Assess honestly: "
            "does it actually solve our problem, or does it solve a narrower "
            "problem (which chart type for which data shape) that doesn't "
            "generalize to Altair8's broader goal (any visual form, any "
            "audience, any business communication)? Be precise about scope: "
            "charts/dashboards vs. general communication structure (branching "
            "narratives, audience-adaptive sequencing, non-linear "
            "presentation) -- the dataviz skill is scoped to the former.\n\n"
            "Also note: neither skill reasons about the audience's prior "
            "knowledge, adapts at runtime to audience behavior, or decides "
            "*whether* a chart/visual is warranted at all versus e.g. a "
            "sentence -- check whether that's true and cite the specific "
            "text that supports or contradicts it (e.g. the dataviz "
            "procedure step 1 does ask 'is this even a chart').\n\n"
            "End with a verdict per provider and an overall verdict: is "
            "Altair8's core research question already solved by any "
            "foundation model's first-party capabilities? If partially "
            "solved, specify exactly which slice."
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
        doc_id=f"foundation-model-scan-task-{task_id}",
        text=report,
        metadata={"agent": "kenji", "type": "foundation_model_capabilities_scan"},
    )
    db.set_memory("kenji", "foundation_model_capabilities_scan", report)
    db.update_task(
        task_id, status="completed", result=report,
        artifact_type="research_brief",
        artifact_payload={"memory_key": "kenji/foundation_model_capabilities_scan"},
    )

    print(f"[{NAME}] Foundation-model capability scan complete.\n\n{report}")


if __name__ == "__main__":
    run()
