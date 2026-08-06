"""Stage 3 -- Component Writer.

The sequential-generation discipline is borrowed from TVIR (write section by
section, each with context from what came before). What is NOT borrowed is
TVIR's context model: TVIR's writer only needs prior prose, because its
output is continuous text. This writer's output is structured components --
prose blocks plus references to interactive visual slots -- so the context
threaded into each section-write call must include what the visuals in
prior sections actually show and support, not just what was said about
them. See schema.SectionContext-shaped dict below (Ingrid's review,
must-fix #2).
"""
import json
import re

from prototype.pipeline.providers import STAGE_CONFIG, complete
from prototype.pipeline.schema import VisualSlot

SYSTEM_PROMPT = """You write one section at a time for a business communication artifact that will be rendered as an interactive web page. You write prose that accurately refers to interactive charts as interactive ("the chart below lets you filter by...") -- never describe a chart as if it were a static image. You have the context of what was written and shown in prior sections; don't repeat it, and don't contradict established interaction patterns."""

PROMPT_TEMPLATE = """SECTION TO WRITE:
Title: {title}
What this section should say: {content_summary}
Audience/goal role of this section: {audience_note}

VISUAL(S) AVAILABLE IN THIS SECTION:
{visuals_desc}

CONTEXT FROM PRIOR SECTIONS (do not repeat, stay consistent with):
{prior_context}

AUDIENCE: {audience}
GOAL: {goal}

Write this section's prose. Output as JSON:
{{
  "prose_blocks": ["<paragraph 1>", "<paragraph 2>", ...],
  "prose_summary": "<1-2 sentence summary of what this section said and showed, for use as context by the next section>"
}}

1-3 prose_blocks. If a visual is available, reference it naturally in the prose (e.g. "as the chart below shows..."). Output ONLY the JSON, no markdown fences."""


def _extract_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text)


def _describe_visuals(visuals: list[VisualSlot]) -> str:
    if not visuals:
        return "(none for this section)"
    lines = []
    for v in visuals:
        if not v.validation_passed:
            status = "FAILED VALIDATION -- do not claim it works, do not describe it as present"
        elif v.content_grounded is False:
            status = "WITHHELD -- structurally fine but failed a content check, do not describe it as present"
        else:
            status = "valid"
        lines.append(f"- [{v.slot_id}] {v.caption} (interactive: {v.spec.get('mark', 'unknown')} chart, {status})")
        if status == "valid":
            values = v.spec.get("data", {}).get("values", [])
            if values:
                # Give the writer the REAL data so it doesn't invent its own
                # numbers that could disagree with what the chart shows --
                # same class of drift the content-grounding check exists to
                # catch, just between Stage 2 and Stage 3 instead of Stage 1
                # and Stage 2.
                sample = json.dumps(values[:5], ensure_ascii=False)
                lines.append(f"  actual chart data (use these exact figures, don't invent your own): {sample}")
    return "\n".join(lines)


def write_section(
    title: str,
    content_summary: str,
    audience_note: str,
    visuals: list[VisualSlot],
    prior_sections: list[dict],
    audience: str,
    goal: str,
) -> dict:
    cfg = STAGE_CONFIG["writer"]

    if prior_sections:
        prior_context = "\n".join(
            f"- \"{p['title']}\": {p['prose_summary']} "
            f"(visuals used: {', '.join(p['visual_slot_ids']) or 'none'}; "
            f"interactions used: {', '.join(p['interactions']) or 'none'})"
            for p in prior_sections
        )
    else:
        prior_context = "(this is the first section)"

    prompt = PROMPT_TEMPLATE.format(
        title=title,
        content_summary=content_summary,
        audience_note=audience_note,
        visuals_desc=_describe_visuals(visuals),
        prior_context=prior_context,
        audience=audience,
        goal=goal,
    )
    raw = complete(cfg["provider"], cfg["model"], SYSTEM_PROMPT, prompt, max_tokens=1200)
    try:
        return _extract_json(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Writer did not return valid JSON for section '{title}'. Raw output:\n{raw}") from e
