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
    # Rewritten 2026-09-15. The original read "in the future, all business
    # communication material will be created by agents" -- unbounded, total,
    # a prediction. Ingrid's falsifiability audit called it decoration:
    # nothing anyone built could contradict it. The founder accepted this
    # version, which stakes something that can actually fail.
    "Within the business communication workflows this product targets, "
    "agent-generated first drafts will become the norm rather than the "
    "exception within five years -- sufficient that designing for AI-first "
    "generation rather than AI-assisted editing is the right bet. FALSIFIED "
    "IF: human-first creation remains dominant in the target segments, in "
    "which case the product concept needs rethinking, not adjusting.",

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

    # Added 2026-09-15, founder-stated, after Ingrid's audit of the
    # twelve-sprint assessment. Hypotheses 1-4 are claims about the world and
    # about this team. 5-8 are claims about the STATE OF KNOWLEDGE the project
    # is building on, and each carries its evidence status in its own text --
    # because the founder originally stated 5 and 6 as a single hypothesis
    # with "we proved this" attached, and only one half of it was proven.
    "LLMs have documented weaknesses in visual and spatial reasoning -- "
    "orientation and reference-frame failures that the retrieved literature "
    "does not explain by data sparsity, and which therefore appear to be "
    "properties of how these models represent space rather than gaps more "
    "training data would close. EVIDENCE STATUS: established (Sprint 1, "
    "arXiv-sourced, review-confirmed). FALSIFIED IF: the failures close "
    "under targeted training or scale, which would make them a data problem "
    "after all. 'Structural' is used in that specific sense and no other.",

    # Reformulated 2026-09-15 on Ingrid's falsifiability audit. The founder
    # first wrote that the knowledge is ABSENT and that this was proven; it
    # is not, and the record points the other way. Sophie then wrote "latent
    # but unreliable", which Ingrid judged an overclaim in the opposite
    # direction: "latent" quietly asserts a MECHANISM (internalised
    # structure) where the live alternative is fluent convention
    # pattern-matching. Both produce the Sprint 6/7 behaviour and they imply
    # different architectures, so the wording must not settle what backlog
    # #23 has not yet measured.
    "Models show audience-and-goal-sensitive form selection that is better "
    "than chance but not reliable -- the mechanism is unresolved. EVIDENCE "
    "STATUS: directional only (Sprints 6 and 7: reasoning demonstrably "
    "shifts with audience and goal, and in the strongest cases switches "
    "medium category; two pilots, single runs per variant, and a "
    "scripted-scenario validity threat named but never quantified or "
    "compensated for). The two live explanations -- internalised structure "
    "that can be elicited, versus fluent reproduction of convention -- are "
    "what backlog #23 exists to discriminate, and no architecture may "
    "depend on one of them until it has. FALSIFIED IF: form selection turns "
    "out to be insensitive to audience and goal once scripted scenarios are "
    "removed. This also decides candidate approach #11: under internalised "
    "structure a corpus supplies a convention prior; under pattern-matching "
    "the same corpus reinforces the ceiling this project exists to break.",

    "No existing system -- commercial, first-party, open-source or academic "
    "-- uses that knowledge at the presentation level with an explicit "
    "audience model. EVIDENCE STATUS: established across four categories and "
    "five sprints, conditional on the literatures actually reached (ACM DL, "
    "CHI, UIST and InfoVis remain unreached, backlog #15). Note this is a "
    "claim about SYSTEMS, not about models, and it is routinely confused with "
    "hypothesis 6.",

    "Business communication output is produced in the browser (HTML and "
    "frontend frameworks). STATUS: an assumption, not a hypothesis -- it "
    "cannot be false, only expensive. The substrate's expressive ceiling is "
    "effectively unlimited for this purpose (Sprints 8, 9 and 11 all rendered "
    "real artifacts there); what is NOT established is the agent's reliable "
    "generation ceiling within it, which is the binding constraint (Sprint 9's "
    "reproduction test: fidelity degrades as visual complexity rises). Per "
    "design principle 4's addendum, what this forecloses is named rather than "
    "ignored: native desktop surfaces and anything not screen-borne. The "
    "price is judged low. FALSIFICATION CONDITION, added 2026-09-15 because "
    "Ingrid judged that reclassifying this as an assumption was shielding a "
    "real risk: the browser is not only an expressive container, it is a "
    "distribution and integration constraint. The assumption is WRONG "
    "rather than merely expensive if target-segment sharing workflows "
    "cannot carry browser-rendered output (the artifact has to live in a "
    "PPTX, a Slides deck or a Teams tab), if PPTX or PDF turns out to be a "
    "non-negotiable enterprise procurement criterion, or if agent "
    "generation fidelity at the target artifact's complexity falls below "
    "usable quality.",

    # The three below are not hypotheses the programme must resolve before
    # proceeding. They are bets it is already making without having said so,
    # surfaced by Ingrid on 2026-09-15 under the instruction to look for what
    # nobody states because everyone shares it. Recorded so that a product
    # path which quietly resolves one of them can be caught doing it.
    "UNSTATED BET A -- that the single artifact is the right unit of "
    "business communication. Everything built so far assumes an output that "
    "is generated, reviewed and consumed as a unit. If communication is "
    "moving toward persistent, queryable structures instead, the programme "
    "has optimised the production of a unit the market is leaving. C1 "
    "already gestures past the artifact with confidence encoding and "
    "expand/collapse, without anyone having asked the question.",

    "UNSTATED BET B -- that the person who commissions an artifact and the "
    "person who reads it want compatible things. A McKinsey deck is not "
    "optimised for the analyst receiving it but for the partner sending it; "
    "form partly performs credibility and intent. If that is right, "
    "optimising for reader comprehension can produce artifacts readers find "
    "clearer and buyers find less impressive -- which is, on Ingrid's "
    "reading, precisely why template libraries sell visual complexity the "
    "research says reduces comprehension. The market may be right for "
    "reasons this programme's frame cannot see.",

    "UNSTATED BET C -- that this is a generation problem rather than a "
    "content problem. Every sprint has treated the content as given. If the "
    "real ceiling is that most communicators have data and opinions rather "
    "than an argument, and that building the deck is how they find out what "
    "they think, then the value is in the friction, and a system that "
    "generates the artifact from inputs removes exactly the part worth "
    "keeping. The north star says humans visualise their communication "
    "TOGETHER WITH agents, not instead of thinking.",
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
