"""C1 Commitment Audit — the audit data structure and its validation.

Implements Mateo's Section 1 specification (mateo/c1_spanning_scaffold_spec),
with the intent decisions Priya settled in priya/c1_build_question_answers.

Two decisions from that exchange are load-bearing here and are enforced in
code rather than left to convention:

1. CONFIDENCE IS ORDINAL, NOT CALIBRATED (Priya, Q1). Scores are the agent's
   honest self-assessment, not probabilities. Nothing in this module treats them
   as interchangeable floats on a common scale -- no arithmetic combination, no
   propagation, no averaging. They are only ever compared against thresholds and
   bucketed into bands.

2. THE AUDIT IS GENERATED IN THE SAME PASS AS THE CONTENT (Priya, Q3). A claim
   cannot exist without its category and confidence, so the schema itself
   forecloses a content-first-annotate-later path. A second-pass audit would
   recreate the exact stage boundary this concept exists to remove -- Sprint 8's
   confabulation failure with an extra stage.

What validation does NOT do, and this is the concept's known open risk
(backlog #24, raised by Priya): it checks the FORM of the audit, never its
CONTENT. A well-formed DAG with plausible scores validates cleanly whether or
not the epistemic classifications are honest. That is the same distinction that
let Sprint 8 ship a structurally perfect chart full of data about a different
subject.
"""
from dataclasses import dataclass, field

CATEGORIES = ("evidence", "inference", "assumption", "assertion")

# Priya endorsed Mateo's three-band stepped encoding (4.6) on the merits:
# with ordinal scores there is no information in the gap between 0.73 and 0.69
# for a continuous encoding to preserve. Thresholds are provisional pending user
# testing. Labels are epistemic words, not numeric ranges -- showing the ranges
# would reimport the false precision through a different door.
BANDS = (
    ("high", 0.7, "well-supported"),
    ("medium", 0.4, "partially supported"),
    ("low", 0.0, "weakly supported"),
)

# Mateo 4.2: no automatic confidence propagation (ordinal scores do not support
# it), but a high-confidence claim resting on much weaker premises is logged for
# whoever reviews the audit. Priya endorsed with one clarification: this warning
# is NEVER shown to the reader. It is an audit-log signal, and surfacing it would
# be noise the reader cannot interpret. She flagged that it must not be lost in
# the build, so it is a first-class return value, not a print statement.
PROPAGATION_WARNING_DELTA = 0.3


@dataclass
class Claim:
    id: str
    text: str
    category: str
    confidence: float
    depends_on: list[str] = field(default_factory=list)
    is_root: bool = False

    def band(self) -> tuple[str, str]:
        """(band_key, reader-facing label). Never returns the numeric score."""
        for key, floor, label in BANDS:
            if self.confidence >= floor:
                return key, label
        return BANDS[-1][0], BANDS[-1][2]


class AuditError(ValueError):
    """A malformed audit. Rejected before rendering, never repaired silently."""


@dataclass
class Audit:
    title: str
    claims: list[Claim]

    def by_id(self) -> dict[str, Claim]:
        return {c.id: c for c in self.claims}

    def root(self) -> Claim:
        roots = [c for c in self.claims if c.is_root]
        return roots[0]

    def children(self, claim_id: str) -> list[str]:
        """The claims this one depends on -- its supports, one level down."""
        return self.by_id()[claim_id].depends_on

    def parents(self, claim_id: str) -> list[str]:
        return [c.id for c in self.claims if claim_id in c.depends_on]


def validate(audit: Audit) -> list[str]:
    """Enforce Mateo's five structural guarantees. Returns audit-log warnings.

    Raises AuditError on anything that makes the PRP algorithm ill-defined.
    Warnings are for the audit log and are never shown to the reader.
    """
    ids = [c.id for c in audit.claims]
    if len(ids) != len(set(ids)):
        raise AuditError("duplicate claim ids")

    index = audit.by_id()
    warnings: list[str] = []

    for c in audit.claims:
        if c.category not in CATEGORIES:
            raise AuditError(f"{c.id}: category {c.category!r} not in {CATEGORIES}")
        if not 0.0 <= c.confidence <= 1.0:
            raise AuditError(f"{c.id}: confidence {c.confidence} outside [0,1]")
        for dep in c.depends_on:
            if dep not in index:
                raise AuditError(f"{c.id}: depends on unknown claim {dep!r}")

    # Guarantee 2: exactly one root.
    roots = [c for c in audit.claims if c.is_root]
    if len(roots) != 1:
        raise AuditError(f"expected exactly one root, found {len(roots)}")
    root = roots[0]

    # Guarantee 1: no cycles. Priya's Q5 answer: reject, never auto-repair --
    # breaking a cycle by dropping an edge silently invents a semantics the
    # agent did not assert.
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {c.id: WHITE for c in audit.claims}

    def visit(node_id: str, trail: list[str]) -> None:
        colour[node_id] = GREY
        for dep in index[node_id].depends_on:
            if colour[dep] == GREY:
                cycle = " -> ".join(trail + [node_id, dep])
                raise AuditError(f"cycle in audit: {cycle}")
            if colour[dep] == WHITE:
                visit(dep, trail + [node_id])
        colour[node_id] = BLACK

    for c in audit.claims:
        if colour[c.id] == WHITE:
            visit(c.id, [])

    # Guarantee 3: every node reaches the root. Anything that does not is doing
    # no epistemic work toward the main claim and does not belong in the map.
    reaches = set()

    def walk(node_id: str) -> None:
        if node_id in reaches:
            return
        reaches.add(node_id)
        for dep in index[node_id].depends_on:
            walk(dep)

    walk(root.id)
    orphans = sorted(set(index) - reaches)
    if orphans:
        warnings.append(
            f"orphaned claims with no path to the root, discarded: {orphans}"
        )

    # Mateo 4.2 / Priya's clarification: log, do not render.
    for c in audit.claims:
        if c.id not in reaches or not c.depends_on:
            continue
        weakest = min(index[d].confidence for d in c.depends_on)
        if c.confidence - weakest > PROPAGATION_WARNING_DELTA:
            warnings.append(
                f"{c.id} ({c.category}, {c.confidence:.2f}) rests on a premise at "
                f"{weakest:.2f} — discrepancy {c.confidence - weakest:.2f} exceeds "
                f"{PROPAGATION_WARNING_DELTA}. Flagged for human review; not shown to reader."
            )

    return warnings


def prune_orphans(audit: Audit) -> Audit:
    """Drop claims with no path to the root, per guarantee 3."""
    index = audit.by_id()
    reaches: set[str] = set()

    def walk(node_id: str) -> None:
        if node_id in reaches:
            return
        reaches.add(node_id)
        for dep in index[node_id].depends_on:
            walk(dep)

    walk(audit.root().id)
    return Audit(title=audit.title,
                 claims=[c for c in audit.claims if c.id in reaches])
