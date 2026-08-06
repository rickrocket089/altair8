"""Sprint 9 Phase B, pattern 1 -- Scrollytelling with pinned visual state.

Ingrid's Phase-A-review condition (must not be faked): the agent itself
must decide which text beat triggers which visual-state change. A prototype
where a human hand-authors the scroll/transition logic and the agent only
generates prose would look like this pattern without testing the actual
capability that makes it interesting. So: ONE LLM call generates both the
narrative beats AND, for each beat, which data category to highlight in the
pinned chart and what the headline number should say -- the mapping from
text to visual state is the thing being tested, not the visuals themselves.
"""
import json
import os
import re

from prototype.pipeline.providers import complete

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

SYSTEM_PROMPT = """You write scrollytelling narratives: a sequence of short text beats, each paired with a specific visual-state change in a pinned chart that stays fixed while the reader scrolls. You decide, for each beat, exactly which data category the visual should highlight and what headline number to show -- this pairing IS the content, not decoration."""

PROMPT_TEMPLATE = """TOPIC: {topic}
AUDIENCE: {audience}
GOAL: {goal}

First, invent 5 data categories with plausible illustrative values relevant to this topic (e.g. departments, regions, product lines -- whatever fits).

Then write 4-6 short narrative beats (1-2 sentences each) that build an argument using this data. For EACH beat, decide which ONE category (by exact name) the pinned chart should highlight while that beat is on screen, and what headline number/stat should display. The reader sees the SAME chart throughout; only the highlighted category and headline change per beat. Make the mapping deliberate -- each beat's text should be about the category it highlights.

Output JSON only:
{{
  "categories": [{{"name": "...", "value": <number>}}, ...],
  "beats": [
    {{"text": "...", "highlight_category": "<exact name from categories, or null to show all equally>", "headline": "<short stat/label for this beat>"}}
  ]
}}"""


def _extract_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text)


def generate(topic: str, audience: str, goal: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(topic=topic, audience=audience, goal=goal)
    raw = complete("anthropic", "claude-sonnet-4-6", SYSTEM_PROMPT, prompt, max_tokens=2000)
    return _extract_json(raw)


def render(data: dict, title: str) -> str:
    categories = data["categories"]
    max_val = max(c["value"] for c in categories) or 1
    beats = data["beats"]

    bars_svg = ""
    bar_w = 100 / len(categories)
    for i, c in enumerate(categories):
        h = (c["value"] / max_val) * 260
        bars_svg += (
            f'<rect class="bar" data-name="{c["name"]}" '
            f'x="{i*bar_w + 1}%" y="{280-h}" width="{bar_w-2}%" height="{h}" rx="3"></rect>\n'
            f'<text class="bar-label" x="{i*bar_w + bar_w/2}%" y="296">{c["name"]}</text>\n'
        )

    beats_html = ""
    for i, b in enumerate(beats):
        hc = json.dumps(b.get("highlight_category"))
        headline = b.get("headline", "")
        beats_html += f'<div class="beat" data-highlight={hc} data-headline="{headline}">{b["text"]}</div>\n'

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>{title} — Scrollytelling Prototype</title>
<style>
  body {{ margin:0; font-family: Georgia, serif; color:#14181a; background:#fff; }}
  .layout {{ display:flex; max-width:1000px; margin:0 auto; }}
  .pinned {{ position:sticky; top:0; width:45%; height:100vh; display:flex; flex-direction:column;
             justify-content:center; padding:2rem; box-sizing:border-box; background:#f4f1ea; }}
  .headline {{ font-size:1.6rem; font-weight:700; color:#20795b; margin-bottom:1rem; min-height:2.4rem; transition:opacity 0.3s; }}
  svg {{ width:100%; height:300px; }}
  .bar {{ fill:#dadfde; transition:fill 0.4s; }}
  .bar.active {{ fill:#20795b; }}
  .bar-label {{ font-size:9px; fill:#6d7679; text-anchor:middle; }}
  .beats {{ width:55%; padding:2rem; box-sizing:border-box; }}
  .beat {{ min-height:70vh; display:flex; align-items:center; font-size:1.3rem; line-height:1.6;
           color:#3c4547; border-left:3px solid #dadfde; padding-left:1.5rem; opacity:0.35; transition:opacity 0.4s; }}
  .beat.in-view {{ opacity:1; border-left-color:#20795b; }}
</style></head>
<body>
<div class="layout">
  <div class="pinned">
    <div class="headline" id="headline"></div>
    <svg viewBox="0 0 100 300" preserveAspectRatio="none">{bars_svg}</svg>
  </div>
  <div class="beats" id="beats">{beats_html}</div>
</div>
<script>
  const beats = document.querySelectorAll('.beat');
  const bars = document.querySelectorAll('.bar');
  const headline = document.getElementById('headline');
  function setState(el) {{
    const hc = el.dataset.highlight;
    bars.forEach(b => b.classList.toggle('active', hc !== 'null' && b.dataset.name === hc));
    headline.textContent = el.dataset.headline || '';
  }}
  const io = new IntersectionObserver((entries) => {{
    entries.forEach(e => {{
      e.target.classList.toggle('in-view', e.isIntersecting);
      if (e.isIntersecting) setState(e.target);
    }});
  }}, {{ threshold: 0.6 }});
  beats.forEach(b => io.observe(b));
  if (beats.length) setState(beats[0]);
</script>
</body></html>"""


if __name__ == "__main__":
    OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "workspace", "outputs", "prototype-runs")
    os.makedirs(OUT_DIR, exist_ok=True)
    topic = "How customer support ticket volume shifted across five product lines after a major release"
    audience = "Product leadership reviewing where to add support staff next quarter"
    goal = "Build a clear, self-paced argument for which product line needs support investment"
    data = generate(topic, audience, goal)
    html_out = render(data, "Support Ticket Shift")
    path = os.path.join(OUT_DIR, "sprint9-scrollytelling.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"Generated {len(data['beats'])} beats over {len(data['categories'])} categories -> {path}")
