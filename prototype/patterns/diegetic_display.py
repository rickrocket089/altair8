"""Sprint 9 Phase B, pattern 4 -- Diegetic information display, NARROWLY
SCOPED per Ingrid's Phase-A review condition.

Ingrid's condition, applied directly: full "diegetic display" requires the
agent to generate a world model of the subject (what are the entities, what
are their visual forms) -- a categorically harder generation problem than
the other 3 patterns, and not what v1 should test. So: the entities and
their visual forms (factory, truck, warehouse, store -- a supply chain
scene) are PRE-SPECIFIED here, hand-built once, not agent-generated. The
ONLY thing the agent decides is the mapping from data dimensions to visual
properties of those existing entities (size, color intensity, connector
thickness, pulse speed) and the actual data values. This tests exactly the
narrower claim Ingrid said v1 should test, not the full-ambition version.
"""
import json
import os
import re

from prototype.pipeline.providers import complete

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

# Pre-specified, fixed scene -- NOT agent-generated. This is the boundary
# Ingrid's review drew: the agent maps data onto this, it doesn't invent it.
ENTITIES = ["factory", "truck", "warehouse", "store"]

SYSTEM_PROMPT = """You map business data onto a FIXED visual scene of a supply chain (factory -> truck -> warehouse -> store, already drawn). You do not invent new entities or change the scene layout. You only decide: what data dimension maps to each entity's size, color intensity, and (for the truck/connectors) pulse speed or thickness -- and generate plausible illustrative values for each entity and connector."""

PROMPT_TEMPLATE = """TOPIC: {topic}
AUDIENCE: {audience}
GOAL: {goal}

The fixed scene has exactly these 4 entities in this order: factory, truck, warehouse, store (truck sits on the connector between factory and warehouse).

For each entity, decide one data dimension relevant to the topic and give it a value from 0.3 to 1.0 (used to scale size and color intensity -- 1.0 = largest/most intense).
For the two connectors (factory->truck->warehouse, warehouse->store), decide a "flow" value from 0.3 to 1.0 (used for connector thickness and animation speed).

Output JSON only:
{{
  "legend": {{"factory": "<what the value represents>", "truck": "<what the value represents>", "warehouse": "<...>", "store": "<...>", "connector_1": "<what flow represents>", "connector_2": "<...>"}},
  "values": {{"factory": <0.3-1.0>, "truck": <0.3-1.0>, "warehouse": <0.3-1.0>, "store": <0.3-1.0>, "connector_1": <0.3-1.0>, "connector_2": <0.3-1.0>}}
}}"""


def _extract_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text)


def generate(topic: str, audience: str, goal: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(topic=topic, audience=audience, goal=goal)
    raw = complete("anthropic", "claude-sonnet-4-6", SYSTEM_PROMPT, prompt, max_tokens=1200)
    return _extract_json(raw)


# Fixed, hand-authored icon shapes (simple, legible at small size) -- this
# is the "world model" a human specified once, not agent-generated.
_ICONS = {
    "factory": '<path d="M0,20 L0,-5 L8,-10 L8,-5 L16,-10 L16,-5 L24,-10 L24,20 Z M4,4 L4,20 M12,4 L12,20 M20,4 L20,20" fill="currentColor" stroke="#14181a" stroke-width="0.5"/>',
    "warehouse": '<path d="M-16,20 L-16,-8 L0,-18 L16,-8 L16,20 Z M-10,20 L-10,6 L10,6 L10,20" fill="currentColor" stroke="#14181a" stroke-width="0.5"/>',
    "store": '<path d="M-14,20 L-14,-4 L14,-4 L14,20 Z M-14,-4 L-17,-10 L17,-10 L14,-4 M-8,20 L-8,10 L8,10 L8,20" fill="currentColor" stroke="#14181a" stroke-width="0.5"/>',
}
_TRUCK = '<path d="M-14,10 L-14,-4 L4,-4 L4,10 M4,2 L14,2 L14,10 L4,10" fill="currentColor" stroke="#14181a" stroke-width="0.5"/><circle cx="-9" cy="12" r="3" fill="#14181a"/><circle cx="8" cy="12" r="3" fill="#14181a"/>'


def render(result: dict, title: str) -> str:
    v = result["values"]
    legend = result.get("legend", {})

    def scale(entity, base):
        return base * (0.6 + v.get(entity, 0.5) * 0.6)

    def color(entity):
        intensity = v.get(entity, 0.5)
        r = int(0xda - intensity * (0xda - 0x20))
        g = int(0xdf - intensity * (0xdf - 0x79))
        b = int(0xde - intensity * (0xde - 0x5b))
        return f"rgb({r},{g},{b})"

    positions = {"factory": 80, "warehouse": 400, "store": 640}
    entity_svgs = ""
    for e in ("factory", "warehouse", "store"):
        s = scale(e, 1.6)
        x = positions[e]
        entity_svgs += (
            f'<g transform="translate({x},220) scale({s})" style="color:{color(e)}">{_ICONS[e]}</g>'
            f'<text x="{x}" y="270" text-anchor="middle" font-size="12" fill="#3c4547">{e} — {legend.get(e, "")}</text>'
        )

    c1, c2 = v.get("connector_1", 0.5), v.get("connector_2", 0.5)
    truck_x = 240
    connectors = (
        f'<line x1="120" y1="220" x2="380" y2="220" stroke="#20795b" stroke-width="{2+c1*10}" opacity="0.6"/>'
        f'<line x1="420" y1="220" x2="600" y2="220" stroke="#a16a17" stroke-width="{2+c2*10}" opacity="0.6"/>'
        f'<g transform="translate({truck_x},220) scale(1.1)" style="color:#4a6fa5">{_TRUCK}'
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="{truck_x-40},0;{truck_x+40},0;{truck_x-40},0" dur="{max(1.5, 4-c1*3)}s" repeatCount="indefinite" additive="sum"/></g>'
    )

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>{title} — Diegetic Display Prototype</title>
<style>
  body {{ margin:0; font-family: Georgia, serif; color:#14181a; background:#fff; max-width:900px; margin:0 auto; padding:3rem 2rem; }}
  h1 {{ font-size:1.5rem; }}
  .note {{ background:#f4f1ea; border-left:3px solid #4a6fa5; padding:1rem 1.3rem; font-size:0.88rem; color:#3c4547; margin-bottom:2rem; }}
  svg {{ border:1px solid #dadfde; border-radius:6px; width:100%; height:auto; }}
</style></head>
<body>
<h1>{title}</h1>
<div class="note">Scene (factory/truck/warehouse/store) is fixed and hand-authored, not generated. The agent only decided: {legend.get('connector_1','')} (route 1 flow), {legend.get('connector_2','')} (route 2 flow), and the size/intensity mapping for each stop.</div>
<svg viewBox="0 0 720 300">
  {connectors}
  {entity_svgs}
</svg>
</body></html>"""


if __name__ == "__main__":
    OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "workspace", "outputs", "prototype-runs")
    os.makedirs(OUT_DIR, exist_ok=True)
    topic = "This quarter's supply chain performance: factory output, transit costs, warehouse inventory pressure, and store-level demand"
    audience = "Operations leadership reviewing where the chain is under strain"
    goal = "See at a glance where the bottleneck is without reading a table"
    result = generate(topic, audience, goal)
    html_out = render(result, "Supply Chain at a Glance")
    path = os.path.join(OUT_DIR, "sprint9-diegetic-display.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"Legend: {result.get('legend')}")
    print(f"Values: {result.get('values')}")
    print(f"-> {path}")
