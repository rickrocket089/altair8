"""Ingrid reviews Kenji's Sprint 14 synthesis -- the real, non-degenerate
FVBS confirmatory result (53.9%, within the pre-registered 40-65% band)
and everything that cascades from it.

Specific things to scrutinize (this sprint's synthesis is much more
hedged than Sprint 13's -- check whether the hedging is genuine
calibration or a way of avoiding a real conclusion the data supports):
the N=3 stratum anomaly reasoning, the ORDER-BEFORE
different-kind-of-null claim, and whether the NOT-IN-SET disaggregation
is actually followed through or just asserted.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")

    synthesis = db.get_memory("kenji", "sprint14_synthesis") or ""
    statistics = db.get_memory("kenji", "sprint14_statistics_summary") or ""
    prereg = (db.get_memory("registrar", "sprint14_preregistration") or "")[:8000]

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Sprint 14 gate: review the confirmatory synthesis before sprint close",
        description="Real, non-degenerate FVBS result this time -- scrutinize the interpretation.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=6000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Review Kenji's Sprint 14 synthesis before Sophie closes the "
            "sprint on it. The core numbers (53.9% confirmatory FVBS rate, "
            "the stratified breakdown, the per-model McNemar results, "
            "26.7% NOT-IN-SET) are real, code-computed arithmetic -- not "
            "something to re-derive. Your job is the interpretation "
            "layered on top of it.\n\n"
            "SPECIFIC CHECKS:\n\n"
            "1. THE READING-B CLAIM (Section 2). Kenji says the 53.9% "
            "result is 'consistent with' but not 'confirms' Reading B "
            "(F1/F2/F3 measures too easy a question). Is this the right "
            "amount of hedging, or is he now UNDER-claiming what a real, "
            "non-degenerate, in-band confirmatory result actually "
            "supports -- the opposite error from Sprint 13, where he was "
            "checked for overclaiming? A result inside a pre-registered "
            "band that itself required real recalibration work to get "
            "right is stronger evidence than 'directionally informative "
            "but not conclusive.' Push on whether his caution here is "
            "genuine calibration or reflexive hedging after being "
            "corrected once before.\n\n"
            "2. THE N=3 STRATUM REASONING (Section 3). Kenji argues the "
            "88% FVBS rate is likely a small-sample artifact, partly by "
            "noting the random-FVBS floor for N=3 is 66.7% (not 33.3%) --"
            "check this arithmetic yourself: is 'chance of FVBS' really "
            "(N-1)/N for a uniform-random model, or did he conflate 'top-1"
            " chance' with 'FVBS chance' incorrectly? Also check whether "
            "his speculation about S06/S11 vocabulary-ceiling "
            "contamination biasing the N=3 stratum is a real mechanism or "
            "an unsupported reach for an explanation.\n\n"
            "3. THE ORDER-BEFORE 'DIFFERENT KIND OF NULL' CLAIM (Section "
            "4). Verify his distinction (Sprint 13 = no variance to test, "
            "Sprint 14 = real test underpowered by NOT_IN_SET attrition) "
            "actually holds against the numbers -- does the data support "
            "'underpowered' rather than simply 'no effect'? Also check "
            "his gemini-specific aside (0 discordant pairs across 13 "
            "usable pairs is itself informative about insensitivity to "
            "ORDER-BEFORE) -- is that a real, defensible read at n=13, or "
            "overreach dressed as a minor note?\n\n"
            "4. THE NOT-IN-SET DISAGGREGATION (Section 5). Confirm Kenji "
            "actually kept the three causes separate throughout, rather "
            "than asserting the disaggregation up front and then "
            "reasoning about '26.7%' as a single number later in the "
            "brief anyway. Also check: does his claim that cause (a) is "
            "a 'substantive finding' rather than noise hold up, or does "
            "he need more evidence than 5 scenario labels to make that "
            "call?\n\n"
            "5. THE OUTPUT-VERIFICATION CAVEAT Kenji states up front "
            "(he did not re-run the underlying scipy computation, "
            "recommends a spot-check). Do that spot-check yourself now: "
            "pick at least 2 numbers from the statistics block and verify "
            "they are internally consistent (e.g., do the stratified "
            "counts sum to the confirmatory total; does the CI make sense "
            "given the n). Report what you checked and whether it held.\n\n"
            "6. ROLE-BOUNDARY CHECK. Section 7 hands three decisions to "
            "Sophie. Confirm this is genuine elevation, not a soft steer "
            "toward one answer (e.g., toward Option 4 in Section 6) "
            "dressed as neutral framing.\n\n"
            "7. GATE VERDICT: PROCEED (Sophie can close on this as-is), "
            "REVISE (name exactly what), or needs rework.\n\n"
            f"=== KENJI'S SYNTHESIS ===\n{synthesis}\n\n"
            f"=== REAL STATISTICS, FOR YOUR OWN SPOT-CHECK ===\n{statistics}\n\n"
            f"=== PRE-REGISTRATION HEAD, FOR REFERENCE ===\n{prereg}\n"
        )}],
    )

    review = result.text
    db.log_usage("ingrid", result.input_tokens, result.output_tokens)

    db.set_memory("ingrid", "sprint14_synthesis_review", review)
    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"sprint14-synthesis-review-task-{task_id}",
        text=review,
        metadata={"agent": "ingrid", "type": "sprint14_synthesis_review"},
    )
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/sprint14_synthesis_review"},
    )

    print(f"[{NAME}] (continuations: {result.continuations})\n\n{review}")
    print(f"\n\n--- {len(review)} chars, stored as ingrid/sprint14_synthesis_review ---")


if __name__ == "__main__":
    run()
