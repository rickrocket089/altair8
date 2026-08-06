"""Stage 2 content-grounding check -- an internal topic-coherence check,
distinct from both the structural validator (reliability_log.py, Question
1: is the spec well-formed) and TVIR's Chart-Source-Consistency metric
(which checks a chart against externally cited references).

Why this exists and why it's not TVIR's CSC check: TVIR's CSC judge looks
at a rendered chart image plus real cited web sources and asks whether the
chart contradicts those sources. That presumes real retrieval happened.
Sprint 8 v1 is Path-A-only (LLM-synthesized illustrative data, no live
retrieval -- see visual_asset_generator.py) so there are no external
sources to check against yet. What v1 needs instead is simpler and purely
internal: does the data Stage 2 actually generated match the topic Stage 1
asked for? This is the check that would have caught the Sprint 8 first-run
bug where a structurally valid chart for an "implementation readiness"
section contained homelessness-service data in a document about urban heat
mitigation -- structural validation is blind to this by design; this check
exists specifically to not be blind to it.

Once Path B (real retrieval) exists in v2, TVIR's actual CSC design
(image + cited sources, LLM-as-judge) becomes the right adoption target
for a second, later check -- this module doesn't replace that, it covers
the gap that exists before it.
"""
import json
import os
import re
from datetime import datetime, timezone

from prototype.pipeline.providers import complete

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "workspace", "outputs", "prototype-runs", "content_grounding_log.jsonl")

SYSTEM_PROMPT = """You are a topic-coherence auditor. You check whether generated chart data actually relates to the topic it was supposed to represent, catching cases where data was generated for a completely different subject than intended. You are strict: generic or superficial overlap doesn't count as coherent if the core subject matter differs."""

PROMPT_TEMPLATE = """SECTION TOPIC: {section_title}
SECTION SHOULD SAY: {content_summary}
CHART WAS SUPPOSED TO SHOW: {visual_description}
WHY THIS CHART WAS REQUESTED: {visual_why}

ACTUAL CHART DATA GENERATED (category/entity values and field names):
{chart_data_summary}

Does the chart data's actual subject matter (the categories/entities it compares -- e.g. what "approach", "item", "scenario" fields actually name) match the section's stated topic? A chart can use the right field NAMES (e.g. "procurement readiness") while containing data about a completely different subject (e.g. homelessness services in a heat-mitigation document) -- that is exactly the failure mode to catch. Field-name matching is not enough; check what the actual category values refer to.

Output JSON only:
{{
  "consistent": true/false,
  "issues": ["<specific mismatch, if any>", ...],
  "reasoning": "<1-2 sentences>"
}}"""


def _extract_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text)


def _summarize_chart_data(spec: dict) -> str:
    values = spec.get("data", {}).get("values", [])
    if not values:
        return "(no data values found)"
    # Sample a few rows rather than dumping potentially large datasets
    sample = values[:5]
    return json.dumps(sample, ensure_ascii=False, indent=2)


def check_coherence(
    section_title: str,
    content_summary: str,
    visual_description: str,
    visual_why: str,
    spec: dict,
) -> dict:
    # Independent judge: the generator (Stage 2) defaults to GPT; the judge
    # here is hardcoded to Claude regardless of STAGE_CONFIG, so the model
    # never grades its own output.
    chart_data_summary = _summarize_chart_data(spec)
    prompt = PROMPT_TEMPLATE.format(
        section_title=section_title,
        content_summary=content_summary,
        visual_description=visual_description,
        visual_why=visual_why,
        chart_data_summary=chart_data_summary,
    )
    raw = complete("anthropic", "claude-sonnet-4-6", SYSTEM_PROMPT, prompt, max_tokens=800)
    try:
        result = _extract_json(raw)
    except json.JSONDecodeError:
        result = {"consistent": None, "issues": ["judge output could not be parsed"], "reasoning": raw[:300]}

    _log(section_title, result)
    return result


def _log(section_title: str, result: dict) -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "section_title": section_title,
        **result,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
