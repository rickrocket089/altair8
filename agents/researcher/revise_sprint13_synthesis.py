"""Kenji applies Ingrid's 5 revisions (R1-R5) to the Sprint 13 synthesis.

Targeted text revision, not new analysis -- same practice as every prior
revision in this project.
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
    original = db.get_memory("kenji", "sprint13_synthesis") or ""
    review = db.get_memory("ingrid", "sprint13_synthesis_review") or ""

    if not original or not review:
        raise RuntimeError("Missing original synthesis or Ingrid's review -- run those first.")

    db.set_memory("kenji", "sprint13_synthesis_v1", original)

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=10000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            f"Your original synthesis:\n\n{original}\n\n"
            f"Ingrid's full review:\n\n{review}\n\n"
            "Apply her 5 revisions (R1 through R5). Targeted text revision, "
            "no new data collection or analysis:\n\n"
            "R1 (mandatory): Section 2's 'tilts toward B' claim must become "
            "'B is a live hypothesis alongside A.' You did not conduct the "
            "contrastive scenario-level analysis (cross-model agreement per "
            "scenario, criterion sensitivity check, or uniquely-determined-"
            "answer analysis) that would actually distinguish A from B -- "
            "say so plainly and remove the directional 'tilts' language.\n\n"
            "R2 (mandatory): Wherever Section 2 uses the probe pass rates "
            "(60-65%) to support Reading B, explicitly re-invoke the "
            "weak-signal caveat: these figures are grounded in Draco's "
            "output alone, and Draco's constraint vocabulary does not "
            "include audience-model terms, which limits what the probe's "
            "pass/fail distinction can be taken to establish about "
            "audience-optimal reasoning specifically.\n\n"
            "R3 (mandatory): Make Section 6's Decision 1 framing internally "
            "consistent with the revised Section 2. Since Section 2 no "
            "longer claims an evidential tilt, Section 6 must not imply "
            "prior analysis already leans toward B. State plainly that the "
            "choice between A and B is genuinely open -- Section 2 "
            "identified B as structurally coherent and worth investigating, "
            "not evidentially favored.\n\n"
            "R4 (recommended): Section 3's claim that fixing McNemar's root "
            "cause requires BOTH a stricter criterion AND harder scenarios "
            "(the 'not vice versa' asymmetry) should be downgraded from a "
            "demonstrated logical consequence to a hypothesis: 'we believe "
            "criterion permissiveness is the binding constraint, but this "
            "should be confirmed by testing whether tighter A-times-G "
            "pairings produce F2 violations under the current criterion "
            "before committing to a criterion redesign.' You had not shown "
            "F1/F2/F3 is invariantly permissive across all possible "
            "scenario difficulty levels, only observed it for these 20.\n\n"
            "R5 (recommended): Section 5's explanation of why Draco can't "
            "support the finer-grained criterion should be sharpened from "
            "'reasoning output is not audience-model-aware' to 'constraint "
            "vocabulary does not include audience-model terms' -- Ingrid's "
            "point: a vocabulary augmentation is a different intervention "
            "than a reasoning-format change, and Sophie needs that "
            "precision to decide on the Draco ruling.\n\n"
            "Leave everything else -- the WHAT THE EVIDENCE SHOWS section, "
            "the two-kinds-of-untestable distinction's core structure, the "
            "JSC-B section, and the rest of Section 5's proposal -- exactly "
            "as it was; Ingrid confirmed those parts are sound. Output the "
            "complete revised synthesis."
        )}],
    )

    revised = result.text
    db.log_usage("kenji", result.input_tokens, result.output_tokens)

    db.set_memory("kenji", "sprint13_synthesis", revised)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id="sprint13-synthesis-revised",
        text=revised,
        metadata={"agent": "kenji", "type": "sprint13_synthesis_revised"},
    )

    print(f"[{NAME}] (continuations: {result.continuations}) Revised synthesis:\n\n{revised}")
    print(f"\n\n--- {len(revised)} chars, stored as kenji/sprint13_synthesis (v1 preserved) ---")


if __name__ == "__main__":
    run()
