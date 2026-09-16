"""Ingrid reviews Kenji's Sprint 13 synthesis -- the real, complete null
result on H1 and everything that cascades from it.

Two things to scrutinize hardest: (1) does Kenji's Reading A/B framing
hold up, or does his own lean toward Reading B overclaim what the evidence
supports; (2) the distinction he draws between the two "untestable"
results (McNemar outcome-variance failure vs K1a/K1b precondition
failure) -- is that a real distinction doing work, or restating the same
fact twice.
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

    synthesis = db.get_memory("kenji", "sprint13_synthesis") or ""
    prereg = (db.get_memory("registrar", "sprint13_preregistration") or "")[:8000]

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Sprint 13 gate: review the confirmatory synthesis before sprint close",
        description="Real null result, real cascading untestability -- scrutinize the interpretation, not just the arithmetic.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=6000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Review Kenji's Sprint 13 synthesis before Sophie closes the "
            "sprint on it. The core result -- 0/60 BASELINE failures, "
            "falsifying the pre-registered 15% floor -- is not in "
            "question; that's real, code-computed arithmetic (scipy "
            "binomtest / exact McNemar), not something to re-derive. Your "
            "job is the interpretation layered on top of it.\n\n"
            "SPECIFIC CHECKS:\n\n"
            "1. READING A VS READING B. Kenji offers two readings of the "
            "null result (models solved structural form selection vs. "
            "F1/F2/F3 measures too easy a question) and says the evidence "
            "'tilts toward B' because the pre-registration's own grounding "
            "argument conceded models 'are not starting from ignorance.' "
            "Is that actually a reason to prefer B over A, or is Kenji "
            "using the SAME evidence that motivated the original 15% "
            "prediction to now explain away its falsification -- which "
            "would be a form of the exact bias Process Review #1 warned "
            "about (fitting analysis to the outcome)? Push on this "
            "specifically: what would you need to see to actually "
            "distinguish A from B, and does Kenji's argument for B meet "
            "that bar or just gesture at it?\n\n"
            "2. THE TWO-KINDS-OF-UNTESTABLE DISTINCTION. Is this doing "
            "real analytical work (different causes, different fixes, as "
            "Kenji claims), or is it restating one fact (zero BASELINE "
            "failures) in two places for rhetorical weight? Check whether "
            "his claim that fixing K1a/K1b would ALSO fix McNemar, but not "
            "vice versa, actually holds up -- work through the logic "
            "yourself rather than accepting his statement of it.\n\n"
            "3. THE PROBE DATA'S ACTUAL STATUS. Kenji says the probe "
            "'produced real data that cannot be applied to K1a/K1b' but "
            "is otherwise usable. Is he giving the probe results (60-65% "
            "pass rates) too much or too little standing given the "
            "underlying ground truth is Draco alone (weak signal, per "
            "Sophie/Ingrid's own prior ruling)? Should this section "
            "re-flag that weak-signal caveat explicitly, or was it "
            "adequately carried forward from the scoring stage?\n\n"
            "4. THE FINER-GRAINED-CRITERION PROPOSAL (Section 5). Is the "
            "'audience-optimal vs structurally-valid' distinction he draws "
            "actually operationalizable, or is it restating the original "
            "H6 problem (internalized structure vs pattern-matching) one "
            "level down without adding anything concrete? Does his claim "
            "that Draco 'alone' can't support this criterion actually "
            "follow, or could Draco's existing output be used differently "
            "without new tooling?\n\n"
            "5. ROLE-BOUNDARY CHECK. Section 6 hands three decisions to "
            "Sophie. Confirm this is genuine elevation (evidence -> "
            "ambiguity -> decision-for-Sophie), not a soft steer toward "
            "one answer dressed as neutral framing -- this is exactly the "
            "pattern Process Review #3 caught him in once already "
            "(Sprint 12).\n\n"
            "6. GATE VERDICT: PROCEED (Sophie can close on this as-is), "
            "REVISE (name exactly what), or the synthesis needs rework "
            "before it's usable for a sprint-closing decision.\n\n"
            f"=== KENJI'S SYNTHESIS ===\n{synthesis}\n\n"
            f"=== PRE-REGISTRATION HEAD, FOR REFERENCE ===\n{prereg}\n"
        )}],
    )

    review = result.text
    db.log_usage("ingrid", result.input_tokens, result.output_tokens)

    db.set_memory("ingrid", "sprint13_synthesis_review", review)
    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"review-task-{task_id}",
        text=review,
        metadata={"agent": "ingrid", "type": "sprint13_synthesis_review"},
    )
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/sprint13_synthesis_review"},
    )

    print(f"[{NAME}] (continuations: {result.continuations})\n\n{review}")
    print(f"\n\n--- {len(review)} chars, stored as ingrid/sprint13_synthesis_review ---")


if __name__ == "__main__":
    run()
