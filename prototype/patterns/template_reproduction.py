"""Sprint 9 addendum -- template-to-HTML reproduction test.

Founder-initiated (2026-08-17), based on an informal test he ran with
another Claude instance: given a template image, the agent rebuilds it
faithfully in HTML/vector graphics, not by re-displaying the original file.

This tests a DIFFERENT capability than patterns/scrollytelling.py,
annotation_led.py, force_directed.py, and diegetic_display.py. Those four
test whether the model can generate a NEW form appropriate to content,
audience, and goal. This tests raw generative-reproduction fidelity: given
an EXISTING image, can the model reconstruct it as vector code at all. It
says nothing about audience/goal-driven form selection (Sprint 6-8's
question) and nothing about inventing new forms (this sprint's other four
patterns) -- it is a third, independent axis: can the agent draw.

Two source images, deliberately varying visual complexity while holding the
subject constant (a rocket), so any fidelity drop-off is attributable to
complexity, not subject-matter noise:
  - rocket_simple.png: flat vector-icon style, ~4 flat colors, no
    perspective, clean geometric shapes.
  - rocket_complex.png: monochrome engraving-style illustration, tilted
    dynamic pose, fine linework, cross-hatching/shading, angled fins.

Hard requirement, enforced by verify_no_raster_reinsertion(): the output
must be pure vector markup. No <img>/<image> tag, no embedded raster data
URI of the source. Trivially re-displaying the original file is not a
"rebuild" -- this is the same no-fake-scaffolding condition Ingrid applied
to the other four Phase-B prototypes, applied here up front rather than
caught after the fact.

Explicitly a 2-item pilot, not a benchmark: single run per image, no
scoring rubric beyond side-by-side visual comparison. Whether fidelity is
"good enough" for any real use is a judgment call for whoever reviews the
comparison, not a number this script produces.
"""
import os
import re

from prototype.pipeline.providers import complete_with_image

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

SYSTEM_PROMPT = """You reconstruct images as hand-authored vector graphics. Given an image, you study its shapes, colors, proportions, and composition, then write a self-contained SVG that reproduces it as closely as you can using vector primitives -- paths, shapes, gradients. You never take the shortcut of embedding the original image: every visual element must be vector markup you authored yourself by reasoning about what you see."""

PROMPT_TEMPLATE = """Reproduce the attached image as closely as possible as a self-contained SVG.

Rules:
- Pure vector output only: <svg> containing <path>/<rect>/<circle>/<ellipse>/<polygon>/<linearGradient>/<radialGradient> etc.
- Do NOT use <img> or <image> tags, and do NOT embed any raster (PNG/JPEG) data URI. Every shape must be vector markup you constructed by looking at the image -- not a copy of it.
- Match proportions, colors, composition, and orientation as closely as you reasonably can.
- Give the outer <svg> a viewBox matching the image's aspect ratio.
- Output ONLY the <svg>...</svg> markup. No explanation, no markdown code fences.
"""


def _extract_svg(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:html|svg|xml)?\s*(<svg.*</svg>)\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r"(<svg[\s\S]*</svg>)", text, re.DOTALL)
    if match:
        return match.group(1)
    return text


def verify_no_raster_reinsertion(svg_markup: str) -> bool:
    """True if clean (pure vector). False if the model cheated by re-embedding the source raster."""
    lowered = svg_markup.lower()
    if "<img" in lowered or "<image" in lowered:
        return False
    if re.search(r"data:image/(png|jpe?g|webp)", lowered):
        return False
    return True


def generate(image_path: str) -> str:
    raw = complete_with_image(
        "anthropic", "claude-sonnet-4-6", SYSTEM_PROMPT, PROMPT_TEMPLATE, image_path, max_tokens=4000
    )
    svg = _extract_svg(raw)
    if not verify_no_raster_reinsertion(svg):
        raise ValueError(
            f"Cheat detected reproducing {image_path}: output re-embeds the source raster "
            "instead of reconstructing it as vector shapes."
        )
    return svg


REVISE_PROMPT_TEMPLATE = """Here is the same image again, and your previous attempt to reproduce it as SVG:

PREVIOUS SVG:
{previous_svg}

A reviewer compared your previous SVG against the original image (attached) and found these specific gaps:

{critique}

Write an IMPROVED SVG that fixes these specific issues while keeping what already worked. Same rules as before:
- Pure vector output only, no <img>/<image>, no raster data URI.
- Output ONLY the <svg>...</svg> markup, nothing else.
"""


def revise(image_path: str, previous_svg: str, critique: str) -> str:
    prompt = REVISE_PROMPT_TEMPLATE.format(previous_svg=previous_svg, critique=critique)
    raw = complete_with_image(
        "anthropic", "claude-sonnet-4-6", SYSTEM_PROMPT, prompt, image_path, max_tokens=4000
    )
    svg = _extract_svg(raw)
    if not verify_no_raster_reinsertion(svg):
        raise ValueError(
            f"Cheat detected revising {image_path}: output re-embeds the source raster "
            "instead of reconstructing it as vector shapes."
        )
    return svg


def render(pairs: list) -> str:
    """pairs: list of (label, source_filename, generated_svg)."""
    blocks = ""
    for label, source_filename, svg in pairs:
        blocks += f"""
<div class="repro-pair">
  <h2>{label}</h2>
  <div class="repro-cols">
    <div class="repro-col">
      <span class="repro-tag">Original (given to the agent)</span>
      <div class="repro-frame"><img src="{source_filename}" alt="{label} original"></div>
    </div>
    <div class="repro-col">
      <span class="repro-tag">Agent-reconstructed &mdash; pure vector, no source pixels used</span>
      <div class="repro-frame">{svg}</div>
    </div>
  </div>
</div>
"""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>Template Reproduction Test</title>
<style>
  body {{ margin:0; font-family: Georgia, serif; color:#14181a; background:#fff; max-width:900px; margin:0 auto; padding:3rem 2rem; }}
  h1 {{ font-size:1.5rem; }}
  h2 {{ font-size:1.1rem; margin: 2rem 0 1rem; }}
  .note {{ background:#f4f1ea; border-left:3px solid #a16a17; padding:1rem 1.3rem; font-size:0.88rem; color:#3c4547; margin-bottom:1rem; }}
  .repro-cols {{ display:flex; gap:1.5rem; flex-wrap:wrap; }}
  .repro-col {{ flex:1; min-width:260px; }}
  .repro-tag {{ display:block; font-size:0.72rem; letter-spacing:0.04em; text-transform:uppercase; color:#6d7679; margin-bottom:0.5rem; }}
  .repro-frame {{ border:1px solid #dadfde; border-radius:6px; padding:1rem; display:flex; align-items:center; justify-content:center; min-height:280px; background:#fafafa; }}
  .repro-frame img, .repro-frame svg {{ max-width:100%; max-height:320px; }}
</style></head>
<body>
<h1>Template Reproduction Test</h1>
<div class="note">The agent receives only the original image on the left. It writes SVG vector markup from scratch to reproduce it -- the result on the right contains none of the source image's pixels.</div>
{blocks}
</body></html>"""


if __name__ == "__main__":
    WORKFILES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "workspace", "workfiles")
    OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "workspace", "outputs", "prototype-runs")
    os.makedirs(OUT_DIR, exist_ok=True)

    items = [
        ("Simple — flat vector icon", "rocket_simple.png"),
        ("Complex — monochrome illustration, tilted", "rocket_complex.png"),
    ]

    pairs = []
    for label, filename in items:
        image_path = os.path.join(WORKFILES_DIR, filename)
        print(f"Generating reproduction for {filename}...")
        svg = generate(image_path)
        pairs.append((label, filename, svg))
        print(f"  -> {len(svg)} chars of SVG, verified clean (no raster reinsertion)")

    html_out = render(pairs)
    out_path = os.path.join(OUT_DIR, "sprint9-template-reproduction.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"-> {out_path}")
