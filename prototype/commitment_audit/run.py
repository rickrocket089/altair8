"""C1 Commitment Audit — run the prototype.

Sprint 11 scope, exactly as Mateo bounded it and no wider: DAG structure, the
primary reading path, the render with expand/collapse, and the category filter,
against a hand-authored audit. The natural-language control mechanism is a
second sprint. A live agent-generated audit is beyond both, and per Priya's Q3
answer is a research question rather than a build task.

Includes a self-test of the PRP algorithm, because the whole point of settling
the specification before building was that the algorithm has a correct answer
that can be checked rather than eyeballed.
"""
import argparse
import os

from prototype.commitment_audit import schema
from prototype.commitment_audit.reading_path import (
    DEFAULT_TAU, compute_prp, bottleneck, load_bearing_weak_claims,
)
from prototype.commitment_audit.renderer import render
from prototype.commitment_audit.sample_audit import SAMPLE

OUT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "workspace", "outputs", "prototype-runs"
)


def self_test() -> None:
    """Check the PRP against its specification rather than against intuition."""
    audit = schema.prune_orphans(SAMPLE)
    index = audit.by_id()

    prp = compute_prp(audit, tau=0.5)
    assert prp, "expected a path at the default threshold"
    assert prp[0] == "root", "PRP must start at the main claim"
    assert not index[prp[-1]].depends_on, "PRP must terminate at a grounded leaf"
    assert all(index[n].confidence >= 0.5 for n in prp), "no claim below threshold"
    for a, b in zip(prp, prp[1:]):
        assert b in index[a].depends_on, f"{b} is not a support of {a}"

    # The short strong chain should beat the longer cost line, which is what
    # "fewest nodes, strongest weakest link" is supposed to mean in practice.
    assert prp == ["root", "legal_risk", "dpa_finding"], f"unexpected PRP: {prp}"

    # Raising the threshold past a link should break the chain, not silently
    # substitute a weaker one.
    assert compute_prp(audit, tau=0.8) == [], "expected no path above 0.8"

    # The unavoidable weak assumption can never appear in the PRP, which is
    # exactly why the renderer surfaces it separately.
    weak = load_bearing_weak_claims(audit, tau=0.5)
    assert "migration_date" in weak, f"expected migration_date load-bearing, got {weak}"
    assert "migration_date" not in prp

    print(f"  self-test passed — PRP {' -> '.join(prp)}, "
          f"bottleneck {bottleneck(audit, prp):.2f}")


def run(tau: float, out_name: str) -> None:
    print("[Mateo Fittipaldi] C1 Commitment Audit prototype")

    raw_warnings = schema.validate(SAMPLE)
    audit = schema.prune_orphans(SAMPLE)
    print(f"  audit validated — {len(SAMPLE.claims)} claims in, "
          f"{len(audit.claims)} after pruning orphans")
    for w in raw_warnings:
        print(f"  audit log: {w}")

    self_test()

    prp = compute_prp(audit, tau=tau)
    print(f"  primary reading path (tau={tau}): {' -> '.join(prp) if prp else '(none)'}")
    weak = load_bearing_weak_claims(audit, tau=tau)
    if weak:
        print(f"  load-bearing claims below threshold: {weak}")

    html = render(audit, prp, tau, raw_warnings)
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, out_name)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  written: {out_path} ({len(html)} chars)")
    print("  NOT verified in a real browser — same limitation flagged in "
          "Sprints 8 and 9; needs a founder pass.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tau", type=float, default=DEFAULT_TAU)
    parser.add_argument("--out", default="sprint11-c1-commitment-audit.html")
    args = parser.parse_args()
    run(args.tau, args.out)
