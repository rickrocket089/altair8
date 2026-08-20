"""C1 — Primary Reading Path (PRP) selection.

Direct implementation of Mateo's Section 2 algorithm
(mateo/c1_spanning_scaffold_spec). Priya adopted his rename in
priya/c1_build_question_answers: "minimum-spanning-argument" was importing a
graph-theoretic guarantee this algorithm does not provide -- minimum spanning
tree is defined over EDGE weights, and here weight lives on nodes. A future
implementer reaching for Kruskal's or Prim's would produce something subtly
wrong. The old term appears in no runnable artifact.

What the PRP is: the shortest chain from the root down to a leaf, using only
claims at or above the confidence threshold, with the strongest possible weakest
link. That is "the fewest nodes that establish the main claim at highest
confidence", operationalised.

Note what this deliberately is NOT: it selects one supporting chain, not every
support the root has. A root with two independent lines of support gets one of
them as the default reading path; the other stays available but collapsed. That
is Mateo's operationalisation, adopted as specified rather than reinterpreted
during the build -- the whole point of settling the spec first was to stop the
implementer inventing semantics the concept never authorised.

Complexity O(V + E). Realistic maps are 5-30 nodes.
"""
from prototype.commitment_audit.schema import Audit

DEFAULT_TAU = 0.5      # Mateo 4.4, endorsed by Priya as a starting midpoint,
TAU_FLOOR = 0.1        # explicitly a guess to be tuned by user testing.
TAU_STEP = 0.1         # "Make it shorter" -> tau += step. Documented as an
                       # arbitrary linear mapping, not a principled one.


def _topological_leaves_first(audit: Audit) -> list[str]:
    """Claims ordered so every claim appears after the claims it depends on."""
    index = audit.by_id()
    order: list[str] = []
    seen: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in seen:
            return
        seen.add(node_id)
        for dep in index[node_id].depends_on:
            visit(dep)
        order.append(node_id)

    for claim in audit.claims:
        visit(claim.id)
    return order


def compute_prp(audit: Audit, tau: float = DEFAULT_TAU) -> list[str]:
    """Return the ordered PRP from root to leaf, or [] if none exists.

    An empty result is a real outcome, not an error: it means no chain of
    claims at or above tau establishes the main claim. Mateo's edge case --
    surface it to the reader rather than silently lowering the threshold.
    """
    index = audit.by_id()
    root = audit.root()

    # Step 1-2: prune below threshold; the root itself must survive.
    eligible = {c.id for c in audit.claims if c.confidence >= tau}
    if root.id not in eligible:
        return []

    order = _topological_leaves_first(audit)

    # Step 3: a node can anchor a valid sub-path if it is a leaf, or if at
    # least one claim it depends on can.
    valid: set[str] = set()
    for node_id in order:
        if node_id not in eligible:
            continue
        deps = index[node_id].depends_on
        if not deps:
            valid.add(node_id)
        elif any(d in valid for d in deps):
            valid.add(node_id)

    if root.id not in valid:
        return []

    # Step 4: DP over the DAG. best[n] = (path length, bottleneck confidence).
    # Shortest path wins; ties broken by the strongest weakest link.
    best: dict[str, tuple[int, float]] = {}
    for node_id in order:
        if node_id not in valid:
            continue
        claim = index[node_id]
        deps = [d for d in claim.depends_on if d in valid]
        if not deps:
            best[node_id] = (1, claim.confidence)
        else:
            chosen = min(deps, key=lambda d: (best[d][0], -best[d][1]))
            length, bottleneck = best[chosen]
            best[node_id] = (length + 1, min(claim.confidence, bottleneck))

    # Step 5: trace the chosen chain back down from the root.
    path = [root.id]
    current = root.id
    while True:
        deps = [d for d in index[current].depends_on if d in valid]
        if not deps:
            break
        current = min(deps, key=lambda d: (best[d][0], -best[d][1]))
        path.append(current)
    return path


def bottleneck(audit: Audit, path: list[str]) -> float | None:
    """The weakest claim on a path -- what the whole chain actually rests on."""
    if not path:
        return None
    index = audit.by_id()
    return min(index[n].confidence for n in path)


def load_bearing_weak_claims(audit: Audit, tau: float = DEFAULT_TAU) -> list[str]:
    """Claims below tau that are the SOLE support of something above them.

    Mateo's edge case was "a low-confidence claim that is structurally
    unavoidable". The first implementation read that globally -- a claim every
    route from the root must cross -- and the self-test caught that this is
    almost never satisfied: any main claim with two independent lines of support
    makes every individual claim globally avoidable, so the check returned
    nothing and would have quietly rendered the feature dead.

    The useful reading is local. A weak claim that is the only thing holding up
    a claim above it is load-bearing: remove it and that branch collapses
    entirely, however healthy the rest of the map looks. Those are what a
    sceptical reader most needs to find, and by construction they can never
    appear in the primary reading path -- so the renderer surfaces them rather
    than leaving them buried under a collapsed node.
    """
    index = audit.by_id()
    root_id = audit.root().id
    load_bearing = []
    for claim in audit.claims:
        if claim.confidence >= tau or claim.id == root_id:
            continue
        sole_support_of = [
            p for p in audit.parents(claim.id)
            if len(index[p].depends_on) == 1
        ]
        if sole_support_of:
            load_bearing.append(claim.id)
    return load_bearing
