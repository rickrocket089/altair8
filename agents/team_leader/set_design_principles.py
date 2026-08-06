"""Admin entrypoint: set/update the team's working hypotheses and design
principles in Postgres. Parallel artifact to the North Star (set_north_star.py)
-- same pattern: a deliberate, logged action, not an inline edit. Founded
2026-08-06, sitting inside DSR's "Define Objectives of a Solution" phase.

HYPOTHESES are falsifiable claims about the world that future research can
confirm or overturn. DESIGN PRINCIPLES are commitments the team makes about
how to build, independent of whether they're provable -- values, not claims.
"""
from agents.permissions import require_tool
from tools import db

HYPOTHESES = [
    "In the future, all business communication material will be created by "
    "agents, based on interaction with a human.",

    "The visual form of a communication artifact should be derived primarily "
    "from audience and goal, not from content type alone.",

    "Human control over agent-generated communication artifacts will be "
    "exercised primarily through iterative natural-language feedback, not "
    "through direct manipulation of visual primitives.",

    "Absent deliberate counter-pressure, the team will gravitate toward "
    "whichever technical framework is easiest for an LLM (Claude Code or "
    "similar) to generate code for -- current frameworks with strong "
    "text+visualization support and good LLM code-generation compatibility "
    "-- rather than the objectively ideal solution. Named as a hypothesis, "
    "not a principle, because adopting it as a principle would quietly "
    "undercut design principle #4 (ask what's ideal, not what fits existing "
    "constraints) -- this is a risk to watch and guard against, not a value "
    "to pursue.",
]

DESIGN_PRINCIPLES = [
    "We optimize first for the quality of the generated result -- getting "
    "the right form and content -- before optimizing the refinement/control "
    "experience around it.",

    "The solution must not be bound to any single foundation model's "
    "capabilities.",

    "We target a user who never has to learn a tool-specific skill -- no "
    "'knowing how to use PowerPoint' as a prerequisite.",

    "We do not constrain generated output to the flat, static, "
    "two-dimensional boxes of legacy formats like PowerPoint. We exploit the "
    "full range of what generative models can actually produce -- arbitrary "
    "icons and imagery, multi-dimensional data views, zoom, interactivity, "
    "motion -- and ask what the ideal representation would be in a world "
    "without today's format constraints, not what merely fits within them. "
    "Addendum: implementation ease is allowed to determine what we prototype "
    "FIRST, but must never lower the ambition of what we're ultimately "
    "trying to build. If the easiest-to-build path and the ideal path "
    "diverge, we name that gap explicitly rather than quietly settling for "
    "the easier one.",
]


def main() -> None:
    require_tool("team_leader", "set_design_principles")
    db.set_memory("team_leader", "hypotheses", "\n\n".join(f"{i+1}. {h}" for i, h in enumerate(HYPOTHESES)))
    db.set_memory("team_leader", "design_principles", "\n\n".join(f"{i+1}. {p}" for i, p in enumerate(DESIGN_PRINCIPLES)))
    print("Hypotheses set:\n\n" + "\n\n".join(HYPOTHESES))
    print("\n\nDesign Principles set:\n\n" + "\n\n".join(DESIGN_PRINCIPLES))


if __name__ == "__main__":
    main()
