"""Entry point for Mateo to generate headshot portraits for the 4 AI
personas (not the founder — his is a real photo, provided separately),
using the OpenAI Images API since Claude has no image-generation of its own.
"""
import argparse
import os

from dotenv import load_dotenv

from agents.developer.persona import NAME
from tools import db, image_gen
from tools.team import TEAM

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "workspace", "outputs", "team-photos"
)


def run(only: list[str] | None = None) -> None:
    db.set_memory("mateo", "status", "online")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    members = TEAM
    if only:
        wanted = {n.lower() for n in only}
        members = [m for m in TEAM if m["name"].split()[-1].lower() in wanted or m["name"].lower() in wanted]

    for member in members:
        task_id = db.create_task(
            created_by="team_leader",
            assigned_to="mateo",
            title=f"Generate headshot: {member['name']}",
            description=member["portrait_prompt"],
        )
        out_path = os.path.join(OUTPUT_DIR, member["photo"])
        image_gen.generate_image(member["portrait_prompt"], out_path)
        db.update_task(task_id, status="completed", result=f"Written to {out_path}")
        print(f"[{NAME}] Generated {member['photo']}")

    print(f"\n[{NAME}] All portraits written to {OUTPUT_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only", nargs="*", help="Regenerate only these members (match on last name), e.g. --only Kenji Solberg"
    )
    args = parser.parse_args()
    run(only=args.only)
