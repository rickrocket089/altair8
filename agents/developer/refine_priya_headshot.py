"""Entry point for Mateo to warm up Priya's v1 headshot.

Founder approved the v1 candidate (dark blazer, composed) but asked for it to
look "a little bit more friendly". This EDITS v1 rather than regenerating from
a reworded prompt: a fresh generation produces a different face, which would
mean re-picking from scratch. tools.image_gen.edit_image keeps the source
portrait and changes only what the prompt asks for.

Two gradations, because "a little friendlier" is a dose, not a switch --
same show-options-founder-chooses pattern used for the logo directions and
the LinkedIn banner concepts.
"""
import argparse
import os

from dotenv import load_dotenv

from agents.developer.persona import NAME
from agents.permissions import require_tool
from tools import db, image_gen

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

CANDIDATE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "workspace", "outputs", "team-photos", "priya-candidates",
)
SOURCE = os.path.join(CANDIDATE_DIR, "priya-v1-composed.png")

PRESERVE = (
    "Keep the same woman, the same face and likeness, the same dark blazer and "
    "white top, the same hairstyle, the same neutral soft-grey studio background, "
    "and the same lighting and photographic style. Change only the expression. "
    "Photorealistic corporate headshot."
)

VARIANTS = [
    {
        "slug": "v5-warm-subtle",
        "prompt": (
            "Soften this portrait's expression slightly: relax the mouth into the "
            "faintest hint of a smile and warm the eyes a little, so she looks "
            "approachable but still composed and serious. Very subtle change. "
            + PRESERVE
        ),
    },
    {
        "slug": "v6-warm-clear",
        "prompt": (
            "Warm this portrait's expression: a gentle closed-mouth smile and "
            "noticeably warmer, friendlier eyes, while staying professional and "
            "composed rather than broadly smiling. "
            + PRESERVE
        ),
    },
]


def run(only: list[str] | None = None) -> None:
    require_tool("mateo", "write_prototype_file")
    db.set_memory("mateo", "status", "online")

    if not os.path.exists(SOURCE):
        raise SystemExit(f"Source portrait not found: {SOURCE}")

    variants = VARIANTS
    if only:
        wanted = {s.lower() for s in only}
        variants = [
            v for v in VARIANTS
            if v["slug"].lower() in wanted or v["slug"].split("-")[0].lower() in wanted
        ]
        if not variants:
            raise SystemExit(f"No variant matched {sorted(wanted)}")

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="mateo",
        title="Warm up Priya headshot v1 (founder feedback)",
        description=(
            "Edit priya-v1-composed.png to a friendlier expression, preserving "
            f"likeness and styling. {len(variants)} gradations for founder selection."
        ),
    )

    written = []
    for variant in variants:
        out_path = os.path.join(CANDIDATE_DIR, f"priya-{variant['slug']}.png")
        image_gen.edit_image(SOURCE, variant["prompt"], out_path)
        written.append(out_path)
        print(f"[{NAME}] Generated priya-{variant['slug']}.png")

    db.update_task(
        task_id,
        status="completed",
        result=f"{len(written)} warmed variants written to {CANDIDATE_DIR}",
        artifact_type="headshot_candidates",
        artifact_payload={
            "source": os.path.basename(SOURCE),
            "method": "images.edit (likeness preserved)",
            "variants": [os.path.basename(p) for p in written],
            "chosen": None,
        },
    )

    print(f"\n[{NAME}] {len(written)} warmed variants written to {CANDIDATE_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", help="e.g. --only v5")
    args = parser.parse_args()
    run(only=args.only)
