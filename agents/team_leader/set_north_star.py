"""Admin entrypoint: set/update the team's North Star in Postgres.

The North Star is expected to change rarely (per founder decision) — this
script exists so updating it is a deliberate, logged action rather than an
inline edit somewhere.
"""
from agents.permissions import require_tool
from tools import db

NORTH_STAR = (
    "We research to deeply understand why today's LLM-generated slides and "
    "visualizations hit a ceiling. Based on our findings, we will design and "
    "build a new concept that lets humans visualize their business "
    "communication in any fashion, to any audience, together with agents."
)


def main() -> None:
    require_tool("team_leader", "set_north_star")
    db.set_memory("team_leader", "north_star", NORTH_STAR)
    print("North Star set:\n\n" + NORTH_STAR)


if __name__ == "__main__":
    main()
