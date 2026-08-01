"""Entry point for Mateo to propose LinkedIn banner concepts: an abstract
visual of prompts/ideas becoming images, in business context, using
Altair8's corporate colors. Marketing collateral, not sprint research --
same "real agent, real run" convention as the earlier logo exploration,
no review gate (this isn't sprint content).
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

# LinkedIn company-page cover photo: 1584x396 (4:1). gpt-image-1 only offers
# fixed sizes (1024x1024 / 1536x1024 / 1024x1536) -- generate at the widest
# landscape option, then center-crop to the exact banner ratio.
GEN_SIZE = "1536x1024"
BANNER_W, BANNER_H = 1584, 396

STYLE_GUIDE = (
    "Muted editorial illustration style, not glossy corporate stock art, not "
    "a gradient-heavy generic AI look. Flat shapes and soft geometric forms, "
    "restrained and precise, like a designed brand illustration. Corporate "
    "palette: deep forest green #20795b and ochre/amber #a16a17 as the two "
    "accent colors, on a warm off-white/cream background (#f4f1ea) with "
    "dark ink #14181a for any silhouette/linework. No readable text, no "
    "letters, no logos, no words anywhere in the image -- purely abstract "
    "shapes and forms. Wide horizontal composition with generous negative "
    "space so a wordmark could be overlaid later without competing with the "
    "artwork. 16:9-ish horizontal banner framing."
)

CONCEPTS = [
    (
        "prompt-into-chart",
        "An abstract illustration of a stream of small glyph-like fragments "
        "and cursor-like marks flowing left to right across the frame and "
        "gradually coalescing into the clean geometric shape of a bar chart "
        "and an ascending line, as if a typed prompt is turning into a "
        "business chart mid-motion. " + STYLE_GUIDE,
    ),
    (
        "constellation-to-dashboard",
        "An abstract illustration of scattered spark/star-like points of "
        "light (four-pointed diamond stars, like a night sky) drifting and "
        "converging on the right side of the frame into the organized "
        "silhouette of a business dashboard panel with a bar chart, a line "
        "chart, and a few rectangular card shapes. " + STYLE_GUIDE,
    ),
    (
        "spark-to-slide",
        "An abstract illustration of a single glowing four-pointed spark on "
        "the left edge of the frame, with faint radiating motion lines, "
        "transforming across the composition into an orderly stack of "
        "flat rectangular slide/card shapes with a simple bar chart inside "
        "one of them, on the right side. " + STYLE_GUIDE,
    ),
]


def run() -> None:
    require_tool("mateo", "write_prototype_file")
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="mateo",
        title="Propose LinkedIn banner concepts",
        description="A few visual concepts: prompts/ideas becoming images, business context, corporate colors, LinkedIn banner format.",
    )

    os.makedirs(OUT_DIR, exist_ok=True)
    saved = []
    for slug, prompt in CONCEPTS:
        raw_path = os.path.join(OUT_DIR, f"{slug}-raw.png")
        banner_path = os.path.join(OUT_DIR, f"{slug}.png")

        image_gen.generate_image(prompt, raw_path, size=GEN_SIZE)

        img = Image.open(raw_path).convert("RGB")
        # Center-crop the 1536x1024 generation down to the 1584:396 (4:1)
        # banner ratio -- crop height, then upscale width to the exact target.
        target_ratio = BANNER_W / BANNER_H
        src_w, src_h = img.size
        crop_h = int(src_w / target_ratio)
        if crop_h > src_h:
            crop_h = src_h
        top = (src_h - crop_h) // 2
        cropped = img.crop((0, top, src_w, top + crop_h))
        banner = cropped.resize((BANNER_W, BANNER_H), Image.LANCZOS)
        banner.save(banner_path)
        saved.append(banner_path)
        print(f"[{NAME}] Saved concept '{slug}' -> {banner_path}")

    db.update_task(
        task_id, status="completed",
        result=f"3 LinkedIn banner concepts generated: {[os.path.basename(p) for p in saved]}",
        artifact_type="design_concepts",
        artifact_payload={"files": saved},
    )
    print(f"[{NAME}] All concepts saved under {OUT_DIR}")


if __name__ == "__main__":
    run()
