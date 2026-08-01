"""Round 2 of Mateo's LinkedIn banner concepts. Founder feedback on round 1
(agents/developer/design_linkedin_banner.py): liked the style and background
color, but bars/line-charts as the destination image read as "oldschool" --
Altair8's actual research bet is that visualization moves beyond static 2D
charts entirely, so the banner should show characters/glyphs resolving into
something more imaginative than a chart to reflect that.
"""
import os

from dotenv import load_dotenv
from PIL import Image

from agents.developer.persona import NAME
from agents.permissions import require_tool
from tools import db, image_gen

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

OUT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "workspace", "outputs", "linkedin-banners"
)

GEN_SIZE = "1536x1024"
BANNER_W, BANNER_H = 1584, 396
# Vertical crop offset tuned by hand against round 1's "prompt-into-chart"
# result: a pure geometric-center crop clipped the top of the artwork more
# than the bottom looked like it needed. Shifting the crop window up by
# this many px (of the 1024-tall source) kept more of the action band.
CROP_UPWARD_SHIFT = 60

STYLE_GUIDE = (
    "Muted editorial illustration style, not glossy corporate stock art, not "
    "a gradient-heavy generic AI look. Flat shapes and soft geometric forms, "
    "restrained and precise, like a designed brand illustration. Corporate "
    "palette: deep forest green #20795b and ochre/amber #a16a17 as the two "
    "accent colors, on a warm off-white/cream background (#f4f1ea) with "
    "dark ink #14181a for any silhouette/linework. No readable text, no "
    "letters, no logos, no words anywhere in the image -- purely abstract "
    "shapes and forms. Wide horizontal composition, most of the visual "
    "interest vertically centered so it survives a tight horizontal-banner "
    "crop, with generous negative space on the far left and right so a "
    "wordmark could be overlaid later without competing with the artwork."
)

CONCEPTS = [
    (
        "glyphs-into-orb",
        "An abstract illustration of a stream of small glyph-like fragments "
        "and cursor-like marks flowing left to right across the frame and "
        "gradually coalescing -- not into a chart or graph, but into a "
        "glowing three-dimensional wireframe sphere made of interlocking "
        "geometric lines and facets, floating in space, like a small "
        "dimensional planet or crystal forming out of scattered symbols. "
        "The wireframe sphere should read as spatial and dimensional, not "
        "flat. " + STYLE_GUIDE,
    ),
    (
        "glyphs-into-flock",
        "An abstract illustration of small glyph-like fragments and "
        "cursor-like marks on the left side of the frame transforming into "
        "a flowing murmuration -- like a flock of birds or a school of "
        "fish made of the same small shapes -- swirling into one continuous "
        "curved ribbon of motion that spirals across the right side of the "
        "frame. Organic, alive, in motion -- not a static grid or chart of "
        "any kind. " + STYLE_GUIDE,
    ),
    (
        "glyphs-into-portal",
        "An abstract illustration of small glyph-like fragments and "
        "cursor-like marks flowing left to right and being drawn into a "
        "large open geometric portal or aperture shape on the right side of "
        "the frame -- a doorway-like oval or rounded-square opening -- "
        "through which an abstract layered, dimensional glow and faint "
        "concentric shapes are visible, suggesting a completely different "
        "space beyond, not a chart or dashboard of any kind. "
        + STYLE_GUIDE,
    ),
]


def run() -> None:
    require_tool("mateo", "write_prototype_file")
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="mateo",
        title="Propose LinkedIn banner concepts (round 2, non-chart)",
        description="Founder wants the destination image to be imaginative/dimensional, not a bar or line chart -- reflects that Altair8 is researching visualization beyond static 2D charts.",
    )

    os.makedirs(OUT_DIR, exist_ok=True)
    saved = []
    for slug, prompt in CONCEPTS:
        raw_path = os.path.join(OUT_DIR, f"{slug}-raw.png")
        banner_path = os.path.join(OUT_DIR, f"{slug}.png")

        image_gen.generate_image(prompt, raw_path, size=GEN_SIZE)

        img = Image.open(raw_path).convert("RGB")
        src_w, src_h = img.size
        crop_h = int(src_w / (BANNER_W / BANNER_H))
        if crop_h > src_h:
            crop_h = src_h
        top = (src_h - crop_h) // 2 - CROP_UPWARD_SHIFT
        top = max(0, min(top, src_h - crop_h))
        cropped = img.crop((0, top, src_w, top + crop_h))
        banner = cropped.resize((BANNER_W, BANNER_H), Image.LANCZOS)
        banner.save(banner_path)
        saved.append(banner_path)
        print(f"[{NAME}] Saved concept '{slug}' -> {banner_path}")

    db.update_task(
        task_id, status="completed",
        result=f"3 non-chart LinkedIn banner concepts generated: {[os.path.basename(p) for p in saved]}",
        artifact_type="design_concepts",
        artifact_payload={"files": saved},
    )
    print(f"[{NAME}] All concepts saved under {OUT_DIR}")


if __name__ == "__main__":
    run()
