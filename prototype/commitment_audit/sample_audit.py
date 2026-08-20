"""A hand-authored sample audit for the C1 prototype.

Hardcoded on purpose. Priya's Q3 answer draws the line precisely: the prototype
tests whether the rendering and interaction model work, NOT whether an agent can
generate an honest audit. Whether a model can produce a well-formed DAG in a
single structured pass -- with accurate dependency tracing and honest confidence
scores -- is a research question with its own backlog item (#24), and assuming
the prototype answers it would be exactly the overclaim this project keeps
catching.

The content is built to exercise the edge cases Mateo specified rather than to
flatter the renderer:
  - an assumption at 0.35 that every route to the root passes through
    (structurally unavoidable weak claim);
  - a high-confidence inference resting on a much weaker premise, to trip the
    propagation warning at delta > 0.3;
  - a second, longer line of support that the PRP will not choose, so the
    collapsed-but-visible behaviour has something real to hide;
  - all four epistemic categories, with assertions deliberately sitting near
    the root where they are most consequential.
"""
from prototype.commitment_audit.schema import Audit, Claim

SAMPLE = Audit(
    title="We should move EU customer data processing to the Frankfurt region",
    claims=[
        Claim(
            id="root", is_root=True, category="inference", confidence=0.72,
            text="We should move EU customer data processing to the Frankfurt region "
                 "in Q1 rather than waiting for the platform migration.",
            depends_on=["legal_risk", "cost_neutral", "timing", "team_capacity"],
        ),

        # --- the chain the PRP should select: short, and strong throughout ---
        Claim(
            id="legal_risk", category="inference", confidence=0.78,
            text="Processing EU customer data outside the EU exposes us to a "
                 "regulatory risk we are currently carrying unmanaged.",
            depends_on=["dpa_finding"],
        ),
        Claim(
            id="dpa_finding", category="evidence", confidence=0.88,
            text="Our external counsel's July review identified the current "
                 "US-region processing as the single highest-severity open item.",
            depends_on=[],
        ),

        # --- longer supporting line: real, but not the shortest route ---
        Claim(
            id="cost_neutral", category="inference", confidence=0.64,
            text="The move is roughly cost-neutral within the first year.",
            depends_on=["infra_quote", "egress_estimate"],
        ),
        Claim(
            id="infra_quote", category="evidence", confidence=0.81,
            text="Frankfurt region pricing quoted by the provider is within 4% of "
                 "current per-unit compute cost.",
            depends_on=[],
        ),
        Claim(
            id="egress_estimate", category="assumption", confidence=0.42,
            text="One-off data egress during migration stays under the volume "
                 "band where charges step up.",
            depends_on=["volume_trend"],
        ),
        Claim(
            id="volume_trend", category="evidence", confidence=0.69,
            text="Monthly processed volume has grown 6-9% per month for five "
                 "consecutive months.",
            depends_on=[],
        ),

        # --- the structurally unavoidable weak claim ---
        # Every route from the root to a leaf through `timing` passes through
        # this assumption. It can never appear in the PRP, which is precisely
        # why the renderer surfaces it separately.
        Claim(
            id="timing", category="inference", confidence=0.58,
            text="Q1 is the last window before the platform migration makes the "
                 "move substantially harder.",
            depends_on=["migration_date"],
        ),
        Claim(
            id="migration_date", category="assumption", confidence=0.35,
            text="The platform migration begins in Q2 and will not slip again.",
            depends_on=[],
        ),

        # --- an assertion the agent is confident in but cannot ground ---
        # Trips the propagation warning: 0.83 resting on a 0.35 premise.
        Claim(
            id="team_capacity", category="assertion", confidence=0.83,
            text="The platform team has capacity to absorb this in Q1.",
            depends_on=["migration_date"],
        ),

        # --- a genuinely orphaned claim ---
        Claim(
            id="competitor_move", category="evidence", confidence=0.74,
            text="A competitor announced an EU-region migration in June.",
            depends_on=[],
        ),
    ],
)

# Two structural cases are exercised deliberately, and an earlier draft of this
# file collapsed both onto the same claim -- which meant the propagation warning
# silently never fired, because the claim that should have tripped it was pruned
# as an orphan before the check ran. Caught by noticing an empty audit log where
# there should have been an entry. They are now separate claims:
#
#   team_capacity   an assertion at 0.83 resting on a 0.35 assumption. Reachable
#                   from the root, so it trips the propagation warning
#                   (delta 0.48 > 0.3) -- the mechanism Priya insisted must not
#                   be lost in the build.
#   competitor_move plausible, well-evidenced, and supporting nothing. Exercises
#                   guarantee 3: anything not doing epistemic work toward the
#                   main claim is pruned with a logged warning.
