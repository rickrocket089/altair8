"""Stage 2 -- Visual Asset Generator.

Data sourcing decision (Ingrid's review, must-fix #1): Path A only for v1 --
the LLM synthesizes plausible chart data from its own knowledge. Every spec
produced here is marked illustrative=True and carries a visible caption
label; live retrieval (Path B) is out of scope, deferred to v2.

This stage also produces the Stage 2 reliability log Ingrid required:
whether the generated Vega-Lite spec passes a structural validity check,
per model. That log is a pipeline-reliability metric, NOT evidence for
Backlog #9 (principled vs. confabulated reasoning) -- see the module
docstring in reliability_log.py for why those are different questions.

v1 scope note (implementation-time simplification, not in the reviewed
proposal but consistent with it): only the "vega-lite" spec_type is
implemented. "svg-placeholder" for non-chart illustrative visuals is left
for v2 -- generating those well means either real image generation (a
separate, slower API call) or hand-authored icon SVGs, and Ingrid's
own review already flagged Stage 2 scope creep as a risk once (data
sourcing). Adding a second visual pathway here would repeat that mistake.
If a section's visual_requirement can't be served by a chart, it is logged
to global_notes instead of silently producing something.
"""
import json
import re

from prototype.pipeline import reliability_log
from prototype.pipeline.providers import STAGE_CONFIG, complete
from prototype.pipeline.schema import VisualSlot

SYSTEM_PROMPT = """You generate Vega-Lite chart specifications. You do not have access to real data -- generate plausible, illustrative numbers appropriate to the described content. This is explicit and expected for this prototype; do not refuse or caveat inside the spec itself."""

PROMPT_TEMPLATE = """Generate a Vega-Lite v5 chart spec for:

SECTION CONTENT (the specific facts, entities, numbers this section is actually about -- your chart data MUST be consistent with this, not invented independently of it):
{content_summary}

CHART DESCRIPTION: {description}
WHY THIS CHART (audience/goal context): {why}
SUGGESTED INTERACTION: {interaction}

Output ONLY a valid Vega-Lite v5 JSON spec (must include "$schema", "data" with inline "values", "mark", and "encoding"). If an interaction was suggested and it's implementable in Vega-Lite (e.g. a selection/filter), include it. If the section content above names specific entities, numbers, or categories, your chart data must use those same specifics, not substitutes or approximations. No markdown fences, no explanation, just the JSON object."""

# A valid Vega-Lite spec expresses its view either as a single view
# ("mark" + "encoding") or as a composite view ("layer", "facet", "repeat",
# "concat", "hconcat", "vconcat"). An earlier version of this check only
# accepted the single-view form and incorrectly flagged valid layered specs
# as failures -- caught by spot-checking a "failure" by hand during Sprint 8.
SINGLE_VIEW_KEYS = {"mark", "encoding"}
COMPOSITE_VIEW_KEYS = {"layer", "facet", "repeat", "concat", "hconcat", "vconcat"}


def _extract_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text)


def _structurally_valid(spec: dict) -> bool:
    """Lightweight structural check -- NOT full Vega-Lite JSON-Schema
    validation. Confirms the shape a renderer needs, not full spec
    correctness. This is the Stage 2 reliability signal: does the LLM
    reliably produce a spec with the fields a renderer requires."""
    has_view = SINGLE_VIEW_KEYS.issubset(spec.keys()) or bool(COMPOSITE_VIEW_KEYS & spec.keys())
    has_data = isinstance(spec.get("data", {}).get("values"), list)
    return "$schema" in spec and has_view and has_data


def generate_visual(slot_id: str, content_summary: str, description: str, why: str, interaction: str) -> VisualSlot:
    cfg = STAGE_CONFIG["visual_asset_generator"]
    prompt = PROMPT_TEMPLATE.format(
        content_summary=content_summary, description=description, why=why, interaction=interaction or "none"
    )
    raw = complete(cfg["provider"], cfg["model"], SYSTEM_PROMPT, prompt, max_tokens=3000)

    try:
        spec = _extract_json(raw)
        valid = _structurally_valid(spec)
    except json.JSONDecodeError:
        spec = {}
        valid = False

    generator_model = f"{cfg['provider']}:{cfg['model']}"
    reliability_log.log_result(slot_id, generator_model, valid, description)

    return VisualSlot(
        slot_id=slot_id,
        spec_type="vega-lite",
        spec=spec,
        caption=description,
        audience_note=why,
        illustrative=True,
        generator_model=generator_model,
        validation_passed=valid,
    )
