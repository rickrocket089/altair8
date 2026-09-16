"""Kenji revises the Sprint 14 synthesis against Ingrid's gate review.

Verdict was REVISE (targeted, not a rework). Required: Section 2's
closing characterization currently blurs criterion confirmation (real,
should be stated plainly) with mechanism uncertainty (real, should stay
open) into one hedge ("directionally informative but not conclusive") --
the opposite error from Sprint 13 (that was overclaim; this is
under-claim). Plus three minor wording fixes Ingrid named specifically.

Founder's own pipeline spot-check (independent of Ingrid's internal-
consistency checks): re-queried blind_scorer/sprint14_fvbs_scores
directly and confirmed 41 FVBS / 76 valid trials matches the statistics
block exactly -- the standing gate condition Ingrid flagged for Sophie's
close is cleared before this revision runs, not deferred past it.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    synthesis = db.get_memory("kenji", "sprint14_synthesis") or ""
    review = db.get_memory("ingrid", "sprint14_synthesis_review") or ""
    if not synthesis or not review:
        raise SystemExit("Missing synthesis or review.")

    if not db.get_memory("kenji", "sprint14_synthesis_v1"):
        db.set_memory("kenji", "sprint14_synthesis_v1", synthesis)
        print(f"[{NAME}] v1 preserved at kenji/sprint14_synthesis_v1")
    else:
        print(f"[{NAME}] v1 already exists -- not overwriting (rerun-safe).")

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 14 synthesis revision: apply Ingrid's targeted REVISE",
        description="Section 2 under-claim fix (primary), 3 minor wording fixes.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=8000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Ingrid's gate verdict on your Sprint 14 synthesis was "
            "REVISE -- targeted, not a rework. Apply exactly her "
            "required changes and nothing else.\n\n"
            "REQUIRED FIX (substantive, the reason for REVISE): Section "
            "2's closing paragraphs ('How confident is this reading' and "
            "'In plain terms for Hypothesis 6') currently blur two "
            "separate things into one hedge -- the criterion confirmation "
            "(real, strongly supported: the FVBS criterion discriminates "
            "and the observed rate landed within the pre-registered band) "
            "and the mechanism question (genuinely open: convention-"
            "reproduction vs. internalized structure). Rewrite these two "
            "paragraphs to state plainly: (a) Sprint 14 CONFIRMS Reading "
            "B's core claim at the level this sprint was powered to test "
            "-- not merely 'consistent with' it -- and (b) the mechanism "
            "behind the gap remains open, which is what Hypothesis 6 and "
            "Backlog #23 exist to resolve. Do not soften (a) into "
            "'directionally informative but not conclusive' -- that "
            "framing under-reports a genuine confirmatory result and is "
            "the opposite error from Sprint 13's overclaim, which Ingrid "
            "is explicitly flagging as equally wrong in the other "
            "direction.\n\n"
            "THREE MINOR FIXES:\n"
            "1. Section 3 (N=3 stratum): note explicitly that the S06/S11 "
            "vocabulary-ceiling-contamination speculation is not just "
            "unconfirmed but COMPUTABLE from existing per-scenario "
            "pipeline data -- say so in those terms, don't just defer it "
            "silently.\n"
            "2. Section 5 (NOT-IN-SET cause a): replace 'a non-trivial "
            "proportion of model-generated form selections reach for "
            "visualization types...' with 'a coherent cluster of model-"
            "generated form selections, across at least 5 scenarios, "
            "reached for visualization types...' -- hold the 'non-"
            "trivial proportion' framing until per-cause trial counts "
            "are in hand.\n"
            "3. Section 4 (gemini aside): replace 'is itself informative "
            "about insensitivity to the ORDER-BEFORE manipulation' with "
            "'is consistent with genuine insensitivity to the ORDER-"
            "BEFORE manipulation, but at n=13 this cannot be "
            "distinguished from coincidental concordance.'\n\n"
            "Reproduce the complete synthesis with these fixes applied "
            "and nothing else changed -- this is a correction pass, not "
            "a rewrite. Do not add analysis, do not restructure sections, "
            "do not soften anything Ingrid did NOT flag.\n\n"
            "NOTE: Ingrid's standing pipeline-verification caveat (41/76 "
            "FVBS count against the actual scoring data) has been "
            "independently re-checked directly against "
            "blind_scorer/sprint14_fvbs_scores and confirmed exact -- "
            "you may state this is cleared, not just recommended.\n\n"
            "=========== INGRID'S FULL REVIEW ===========\n"
            f"{review}\n\n"
            "=========== YOUR SYNTHESIS TO REVISE ===========\n"
            f"{synthesis}\n\n"
            "Output the complete revised synthesis. No preamble, no "
            "summary of what you changed -- just the document."
        )}],
    )

    revised = result.text
    db.log_usage("kenji", result.input_tokens, result.output_tokens)

    db.set_memory("kenji", "sprint14_synthesis", revised)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"sprint14-synthesis-v2-task-{task_id}",
        text=revised,
        metadata={"agent": "kenji", "type": "sprint14_synthesis", "version": 2},
    )
    db.update_task(
        task_id, status="completed", result=revised,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/sprint14_synthesis", "version": 2},
    )

    print(f"[{NAME}] (continuations: {result.continuations})\n\n{revised}")
    print(f"\n\n--- v2 stored at kenji/sprint14_synthesis, {len(revised)} chars ---")


if __name__ == "__main__":
    run()
