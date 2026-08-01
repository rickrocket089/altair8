"""Targeted regeneration of the 'glyphs-into-portal' banner concept (the one
the founder picked). Feedback: the original scattered glyphs too loosely --
he wants a clear converging beam/stream of glyphs narrowing into the portal,
like the flow in the 'prompt-into-chart' concept from round 1.
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

STYLE_GUIDE = (
    "Muted editorial illustration style, not glossy corporate stock art, not "
    "a gradient-heavy generic AI look. Flat shapes and soft geometric forms, "
    "restrained and precise, like a designed brand illustration. Corporate "
    "palette: deep forest green #20795b and ochre/amber #a16a17 as the two "
    "accent colors, on a warm off-white/cream background (#f4f1ea) with "
    "dark ink #14181a for any silhouette/linework. No readable text, no "
    "letters, no logos, no words anywhere in the image -- purely abstract "
    "shapes and forms."
)

PROMPT = (
    "An abstract illustration whose core idea is TRANSFORMATION: small "
    "glyph-like fragments and cursor-like marks (representing prompts and "
    "ideas) begin distinct and sharply separate on the left side of the "
    "frame, then travel together along a single winding, curving path -- "
    "like a river that bends and curls, NOT a straight line or diagonal -- "
    "and as they travel, they gradually lose their individual sharp glyph "
    "shapes, smearing and merging into each other, until by the right side "
    "of the frame they have fully dissolved into smooth, continuous, "
    "concentric layered rings of color -- the glyphs do not fly INTO a "
    "separate pre-existing portal object, they themselves gradually BECOME "
    "the portal. The portal/aperture shape on the right is made of the same "
    "substance as the glyphs, just later in its transformation -- one "
    "continuous material progression from many small sharp fragments to "
    "one smooth layered glowing form, like a visual metaphor for iterative "
    "prompts becoming a finished visualization.\n\n"
    "CRITICAL composition constraint: this is being composed from scratch "
    "for an extremely wide, short letterbox banner, roughly 5.9:1 "
    "width:height (much wider and shorter than a normal photo). Compose the "
    "ENTIRE illustration -- from the first distinct glyph to the fully "
    "formed portal shape -- confined within a thin horizontal ribbon "
    "running through the exact vertical center of the frame, occupying "
    "only the middle 20% of the frame's height. Leave large, genuinely "
    "empty cream margins filling the top ~40% and bottom ~40% of the frame "
    "with nothing in them. The winding path can curve and loop within that "
    "thin ribbon, but must never approach the top or bottom edge of the "
    "image. The finished portal shape itself must be short and wide -- "
    "flattened, like a wide lens or porthole, not a tall archway -- so its "
    "full height comfortably fits inside that same thin central ribbon "
    "without touching the top or bottom edges. " + STYLE_GUIDE
)

BANNER_SIZES = {
    "1128x191": (1128, 191),
    "1584x396": (1584, 396),
}


def run() -> None:
    require_tool("mateo", "write_prototype_file")
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="mateo",
        title="Regenerate 'glyphs-into-portal' banner with a clearer glyph beam",
        description="Founder picked this concept but wants a converging stream/beam of glyphs into the portal, matching the flow style of round 1's chart concept.",
    )

    os.makedirs(OUT_DIR, exist_ok=True)
    raw_path = os.path.join(OUT_DIR, "glyphs-into-portal-v4-raw.png")
    image_gen.generate_image(PROMPT, raw_path, size=GEN_SIZE)

    img = Image.open(raw_path).convert("RGB")
    src_w, src_h = img.size
    saved = []
    for label, (target_w, target_h) in BANNER_SIZES.items():
        ratio = target_w / target_h
        crop_h = min(int(src_w / ratio), src_h)
        top = max(0, min((src_h - crop_h) // 2, src_h - crop_h))
        cropped = img.crop((0, top, src_w, top + crop_h))
        banner = cropped.resize((target_w, target_h), Image.LANCZOS)
        out_path = os.path.join(OUT_DIR, f"glyphs-into-portal-v4-{label}.png")
        banner.save(out_path)
        saved.append(out_path)
        print(f"[{NAME}] Saved {label} -> {out_path}")

    db.update_task(
        task_id, status="completed",
        result=f"Regenerated portal concept with clearer glyph beam: {[os.path.basename(p) for p in saved]}",
        artifact_type="design_concepts",
        artifact_payload={"files": saved},
    )


if __name__ == "__main__":
    run()
