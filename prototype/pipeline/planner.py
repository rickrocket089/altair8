"""Stage 1 -- Audience-Aware Planner.

Adapted from TVIR's planning stage (parse task -> structured outline with
visual requirements attached), with one real change: TVIR's planner has no
concept of audience or goal. Here, audience and goal are first-class input
fields the planner must reason about explicitly for every section -- not
generic content structuring.

v1 requires explicit audience/goal input (Ingrid's review: implicit
extraction is deferred to v2 so failures are diagnosable to the right
stage).
"""
import json
import re

from prototype.pipeline.providers import STAGE_CONFIG, complete

SYSTEM_PROMPT = """You are the planning stage of a content-generation pipeline. Given a request, an explicit audience, and an explicit goal, produce a structured outline. For every section, you must reason about what this specific audience needs from this specific section to achieve the stated goal -- not just what content belongs there."""

PROMPT_TEMPLATE = """REQUEST: {request}
AUDIENCE: {audience}
GOAL: {goal}

Produce a structured outline as JSON with this exact shape:

{{
  "title": "<overall title>",
  "sections": [
    {{
      "id": "<short slug, e.g. 'intro'>",
      "title": "<section title>",
      "content_summary": "<what this section says, 1-3 sentences>",
      "visual_requirement": {{
        "needed": true,
        "description": "<what chart/visual is needed>",
        "why": "<why THIS visual serves THIS audience's THIS goal, specifically -- not a generic justification>"
      }},
      "audience_note": "<what this section is doing for the stated decision-maker/reader -- must reference the actual audience and goal given above, not be generic>",
      "suggested_interaction": "<e.g. 'filter by category', 'hover for detail' -- or 'none' if a static view suffices>"
    }}
  ]
}}

3-5 sections. Not every section needs a visual (set "needed": false if prose alone serves the audience/goal better -- this is itself a real decision, don't default to "always needs a chart").

Output ONLY the JSON, no other text, no markdown code fences."""


def _extract_json(text: str) -> dict:
    text = text.strip()
    # tolerate markdown fences even though we asked for none
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text)


def plan(request: str, audience: str, goal: str) -> dict:
    cfg = STAGE_CONFIG["planner"]
    prompt = PROMPT_TEMPLATE.format(request=request, audience=audience, goal=goal)
    raw = complete(cfg["provider"], cfg["model"], SYSTEM_PROMPT, prompt, max_tokens=3000)
    try:
        return _extract_json(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Planner did not return valid JSON. Raw output:\n{raw}") from e
