"""Sprint 9 Phase B, pattern 3 -- Force-directed relationship graph.

Ingrid's Phase-A-review condition: the generation problem here is
classification (recognize this is relational, not a magnitude-comparison
problem) followed by extraction (entities + relationships). The prompt
forces both steps explicitly so the "is this actually relational" judgment
is visible, not assumed.
"""
import json
import os
import re

from prototype.pipeline.providers import complete

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

SYSTEM_PROMPT = """You identify when business content is fundamentally about relationships between entities (who connects to whom, and how strongly) rather than magnitude comparison, and extract that structure as a node/edge graph."""

PROMPT_TEMPLATE = """TOPIC: {topic}
AUDIENCE: {audience}
GOAL: {goal}

Step 1: confirm (briefly) why this content is a relational-structure problem, not a magnitude-comparison problem -- what would be lost if this were forced into a bar chart or table instead?
Step 2: generate 10-16 nodes (entities, with a short "group" or "category" label for coloring) and 12-24 edges (source, target, weight from 1-10 indicating relationship strength) that plausibly represent this topic.

Output JSON only:
{{
  "rationale": "<step 1 answer, 1-2 sentences>",
  "nodes": [{{"id": "...", "group": "..."}}, ...],
  "edges": [{{"source": "...", "target": "...", "weight": <1-10>}}, ...]
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
    graph_json = json.dumps({"nodes": result["nodes"], "links": result["edges"]})
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>{title} — Force-Directed Prototype</title>
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<style>
  body {{ margin:0; font-family: Georgia, serif; color:#14181a; background:#fff; max-width:900px; margin:0 auto; padding:3rem 2rem; }}
  h1 {{ font-size:1.5rem; }}
  .rationale {{ background:#f4f1ea; border-left:3px solid #20795b; padding:1rem 1.3rem; font-size:0.95rem; color:#3c4547; margin-bottom:2rem; }}
  #graph {{ border:1px solid #dadfde; border-radius:6px; }}
  .link {{ stroke:#c8cccb; }}
  .node text {{ font-size:10px; fill:#3c4547; }}
</style></head>
<body>
<h1>{title}</h1>
<div class="rationale"><strong>Why this is relational:</strong> {result.get('rationale', '')}</div>
<svg id="graph" width="820" height="520"></svg>
<script>
  const data = {graph_json};
  const groups = [...new Set(data.nodes.map(n => n.group))];
  const color = d3.scaleOrdinal().domain(groups).range(["#20795b","#a16a17","#4a6fa5","#8a5fb5","#c2564a","#5a9e7a"]);
  const svg = d3.select("#graph");
  const width = 820, height = 520;
  const sim = d3.forceSimulation(data.nodes)
    .force("link", d3.forceLink(data.links).id(d => d.id).distance(d => 140 - d.weight * 6))
    .force("charge", d3.forceManyBody().strength(-180))
    .force("center", d3.forceCenter(width/2, height/2))
    .force("collide", d3.forceCollide(28));
  const link = svg.append("g").selectAll("line").data(data.links).join("line")
    .attr("class","link").attr("stroke-width", d => Math.max(1, d.weight/2));
  const node = svg.append("g").selectAll("g").data(data.nodes).join("g").attr("class","node")
    .call(d3.drag().on("start", dragstarted).on("drag", dragged).on("end", dragended));
  node.append("circle").attr("r", 16).attr("fill", d => color(d.group)).attr("stroke","#fff").attr("stroke-width",1.5);
  node.append("text").text(d => d.id).attr("text-anchor","middle").attr("dy", 30);
  sim.on("tick", () => {{
    link.attr("x1", d=>d.source.x).attr("y1", d=>d.source.y).attr("x2", d=>d.target.x).attr("y2", d=>d.target.y);
    node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
  }});
  function dragstarted(e,d){{ if(!e.active) sim.alphaTarget(0.3).restart(); d.fx=d.x; d.fy=d.y; }}
  function dragged(e,d){{ d.fx=e.x; d.fy=e.y; }}
  function dragended(e,d){{ if(!e.active) sim.alphaTarget(0); d.fx=null; d.fy=null; }}
</script>
</body></html>"""


if __name__ == "__main__":
    OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "workspace", "outputs", "prototype-runs")
    os.makedirs(OUT_DIR, exist_ok=True)
    topic = "Which internal teams have actually collaborated on shipped projects over the past year, and how often"
    audience = "A new VP of Engineering trying to understand real (not org-chart) working relationships"
    goal = "Reveal collaboration clusters and isolated teams that the org chart hides"
    result = generate(topic, audience, goal)
    html_out = render(result, "Real Collaboration Network")
    path = os.path.join(OUT_DIR, "sprint9-force-directed.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"Rationale: {result.get('rationale')}")
    print(f"{len(result['nodes'])} nodes, {len(result['edges'])} edges -> {path}")
