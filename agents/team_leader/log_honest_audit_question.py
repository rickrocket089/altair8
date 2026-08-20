"""Logs the honest-audit research question Priya raised while answering the
C1 build questions.

She raised it unprompted, in the "what I am still worried about" section, as the
thing she is most concerned by. It is not answered by the C1 rendering study and
should not be allowed to fade as the prototype starts working and looking good.

S7 exists for exactly this: a lead surfaced mid-sprint gets logged systematically
rather than remembered.
"""
from agents.permissions import require_tool
from tools import db

TITLE = "Test whether the agent can produce an HONEST epistemic audit, not just a well-formed one"

DESCRIPTION = """Raised by Priya (2026-08-20) while answering the C1 build
questions -- unprompted, as the thing she is most worried about. Distinct from
the C1 rendering study and not answered by it.

C1 assumes that when the agent classifies a claim as an inference at confidence
0.6, the claim really is an inference and the agent really is about that
confident. The entire value of the visual encoding rests on that assumption, and
nothing in the architecture enforces it. A well-formed DAG with plausible scores
and consistent dependency chains renders correctly and looks rigorous whether or
not the classifications are accurate.

Structural validation checks the FORM of the audit, never its CONTENT. That is
the identical distinction that let Sprint 8 ship a structurally perfect chart
full of data about an entirely different subject.

Priya's framing of the risk: if the agent systematically over-classifies weak
assertions as evidence, C1 becomes a more sophisticated version of the problem
it was built to solve -- confident-looking output wrapped in a navigable
structure that carries EXTRA authority precisely because it appears to be the
agent's own honest self-account.

CONSEQUENCE FOR THE PLANNED FALSIFICATION STUDY, which she also names: that
study tests whether readers with the audit outperform readers without it at
finding the weakest claim. It assumes the audit is honest. If the audit
systematically flatters, the study may find the audit group confidently agreeing
with the agent's designated weakest claim rather than the real one -- and
whether that is better or worse than the control condition is not obvious.

RELATED OPEN QUESTION, from her Q3 answer: can a model reliably produce the
audit in a SINGLE structured pass? Single-pass is required -- a second-pass audit
that reviews already-generated content recreates the exact stage boundary C1
exists to remove, and would be Sprint 8's failure mode with an extra stage. She
is genuinely uncertain this is achievable at the quality the concept requires.
Kenji's retrieval separately surfaced work showing LLMs have demonstrable
calibration problems when asked to verbalise confidence as scores.

This is a behavioural research question. It belongs with the deep-analysis
sprint (backlog #23), not the C1 build sprint."""


def run() -> None:
    require_tool("team_leader", "write_backlog")
    if TITLE in {i["title"] for i in db.list_backlog_items()}:
        print("= backlog item already exists.")
        return
    item_id = db.create_backlog_item(
        title=TITLE, description=DESCRIPTION, proposed_by="priya", priority="high",
    )
    print(f"+ backlog [high] id={item_id}: {TITLE}")


if __name__ == "__main__":
    run()
