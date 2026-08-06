"""Sprint 9 Phase B, pattern 2 -- Annotation-led reading path.

Ingrid's Phase-A-review condition: this pattern's real test is whether the
agent can identify THE single most important insight in a dataset and
commit to marking it directly in the visual layer -- not describe it in
surrounding prose. The prompt forces this as an explicit, separate
reasoning step (identify + justify the ONE point) before the chart spec is
generated, so the annotation isn't decorative.
"""
import json
import os
import re

from prototype.pipeline.providers import complete

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

SYSTEM_PROMPT = """You are given a business scenario and must produce a chart whose primary job is to make ONE specific insight impossible to miss, via a direct visual annotation (not a caption, not surrounding text -- an annotation embedded in the chart itself, pointing at the specific data point). You commit to a single interpretation; you don't hedge by annotating everything."""

PROMPT_TEMPLATE = """TOPIC: {topic}
AUDIENCE: {audience}
GOAL: {goal}

Step 1: invent a plausible illustrative dataset (a time series or category comparison, your choice, appropriate to the topic) -- 6-10 data points.
Step 2: identify the ONE data point that matters most for this audience and goal. State why in one sentence.
Step 3: produce a Vega-Lite v5 spec that is a base chart (line or bar) LAYERED with an annotation for that one point: a rule/point mark plus a text label placed at or near it, stating the insight in a few words. Everything else in the chart should read as context for that one annotated point, not compete with it.

Output JSON only:
{{
  "insight": "<the one-sentence justification from step 2>",
  "spec": {{ ...complete Vega-Lite v5 spec, must include "$schema", "data" with inline "values", and a "layer" with the base chart plus the annotation layer(s)... }}
}}"""


def _extract_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text)


def generate(topic: str, audience: str, goal: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(topic=topic, audience=audience, goal=goal)
    raw = complete("anthropic", "claude-sonnet-4-6", SYSTEM_PROMPT, prompt, max_tokens=2500)
    return _extract_json(raw)


def render(result: dict, title: str) -> str:
    spec = result["spec"]
    spec.setdefault("width", 600)
    if isinstance(spec.get("width"), (int, float)):
        spec["width"] = min(spec["width"], 620)
    spec_json = json.dumps(spec)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>{title} — Annotation-Led Prototype</title>
<script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
<style>
  body {{ margin:0; font-family: Georgia, serif; color:#14181a; background:#fff; max-width:800px; margin:0 auto; padding:3rem 2rem; }}
  h1 {{ font-size:1.5rem; }}
  .insight {{ background:#f4f1ea; border-left:3px solid #a16a17; padding:1rem 1.3rem; font-size:0.95rem; color:#3c4547; margin-bottom:2rem; }}
  #chart {{ max-width:100%; overflow-x:auto; }}
</style></head>
<body>
<h1>{title}</h1>
<div class="insight"><strong>Agent's identified insight:</strong> {result.get('insight', '')}</div>
<div id="chart"></div>
<script>vegaEmbed('#chart', {spec_json}, {{actions: false}});</script>
</body></html>"""


if __name__ == "__main__":
    OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "workspace", "outputs", "prototype-runs")
    os.makedirs(OUT_DIR, exist_ok=True)
    topic = "Monthly churn rate for a subscription product over the last 12 months"
    audience = "The CEO, scanning a board pre-read the night before a meeting"
    goal = "Make sure the CEO doesn't miss the one month that actually needs explaining"
    result = generate(topic, audience, goal)
    html_out = render(result, "Churn Rate — What Needs Explaining")
    path = os.path.join(OUT_DIR, "sprint9-annotation-led.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"Insight identified: {result.get('insight')}")
    print(f"-> {path}")
