"""Entry point for Mateo to generate candidate headshots for Priya Raghunathan,
the Concept Designer (sixth agent, added 2026-08-19).

Unlike generate_team_photos.py, which produced one portrait per member, this
generates several variants of the same person so the founder can pick -- the
same "show options, founder chooses" pattern used for the logo directions and
the LinkedIn banner concepts.

Every variant deliberately shares the house portrait style already established
by the existing five (neutral soft-grey studio background, natural lighting,
85mm portrait lens, shallow depth of field, photorealistic). Only expression
and attire vary, so whichever is picked still sits alongside the others on the
website without looking like a different shoot.

Variants are written to team-photos/priya-candidates/. The chosen one gets
copied to team-photos/priya.png, which is the path tools/team.py expects.
"""
import argparse
import os

from dotenv import load_dotenv

from agents.developer.persona import NAME
from agents.permissions import require_tool
from tools import db, image_gen

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "workspace", "outputs", "team-photos", "priya-candidates",
)

HOUSE_STYLE = (
    "neutral soft-grey studio background, natural lighting, shot on a DSLR "
    "with an 85mm portrait lens, shallow depth of field, photorealistic."
)

BASE = "Professional corporate headshot photo of a 41-year-old British Indian woman, "

VARIANTS = [
    {
        "slug": "v1-composed",
        "prompt": BASE + "thoughtful confident expression, dark blazer, " + HOUSE_STYLE,
    },
    {
        "slug": "v2-warm",
        "prompt": BASE + "warm genuine smile, approachable expression, "
                         "smart-casual knit top, " + HOUSE_STYLE,
    },
    {
        "slug": "v3-considering",
        "prompt": BASE + "calm considering expression, slight head tilt, "
                         "open-collar shirt under a textured jacket, " + HOUSE_STYLE,
    },
    {
        "slug": "v4-direct",
        "prompt": BASE + "direct steady gaze, quietly assured expression, "
                         "dark high-neck top, " + HOUSE_STYLE,
    },
]


def run(only: list[str] | None = None) -> None:
    require_tool("mateo", "write_prototype_file")
    db.set_memory("mateo", "status", "online")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

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
        title="Generate candidate headshots: Priya Raghunathan (Concept Designer)",
        description=(
            f"{len(variants)} variants in the established house portrait style, "
            "for founder selection."
        ),
    )

    written = []
    for variant in variants:
        out_path = os.path.join(OUTPUT_DIR, f"priya-{variant['slug']}.png")
        image_gen.generate_image(variant["prompt"], out_path)
        written.append(out_path)
        print(f"[{NAME}] Generated priya-{variant['slug']}.png")

    db.update_task(
        task_id,
        status="completed",
        result=f"{len(written)} candidate headshots written to {OUTPUT_DIR}",
        artifact_type="headshot_candidates",
        artifact_payload={
            "output_dir": OUTPUT_DIR,
            "variants": [os.path.basename(p) for p in written],
            "chosen": None,
        },
    )

    print(f"\n[{NAME}] {len(written)} candidates written to {OUTPUT_DIR}")
    print("[Next] Founder picks one; copy it to team-photos/priya.png "
          "(the path tools/team.py expects).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only", nargs="*",
        help="Generate only these variants, e.g. --only v2 v4",
    )
    args = parser.parse_args()
    run(only=args.only)
