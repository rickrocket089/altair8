"""Entry point for Naledi to revise the Sprint 6 behavioral reasoning test
per Ingrid's review. Reads her original brief + Ingrid's critique and
produces a revised version that becomes the new current version
(naledi/behavioral_reasoning_test).
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher_visual.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))


def run() -> None:
    require_tool("naledi", "write_cognitive_annotation")
    original = db.get_memory("naledi", "behavioral_reasoning_test") or ""
    review = db.get_memory("ingrid", "sprint6_review") or ""

    if not original or not review:
        raise RuntimeError("Missing original brief or Ingrid's review — run those first.")

    db.set_memory("naledi", "behavioral_reasoning_test_v1", original)

    task_id = db.create_task(
        created_by="ingrid",
        assigned_to="naledi",
        title="Revise Sprint 6 behavioral reasoning test per Ingrid's review",
        description="Apply Ingrid's 3 revision instructions.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Your original brief:\n\n{original}\n\n"
                    f"Ingrid's full Sprint 6 review:\n\n{review}\n\n"
                    "Apply her 3 revision instructions specifically -- this "
                    "is a targeted revision, not new research:\n\n"
                    "1. Remove the '60/40' confidence estimate entirely. "
                    "Replace it with an explicit statement that this pilot "
                    "produces directional evidence, not a quantifiable "
                    "probability -- the evidence is directionally "
                    "consistent with principled reasoning being present in "
                    "some cases, but insufficient to quantify how often. "
                    "State plainly that the form-prediction probe (revised, "
                    "see point 3) is what would actually allow probability "
                    "estimation.\n\n"
                    "2. Add explicit annotations on the cross-model verdicts "
                    "(Pair A: Claude shows stronger audience-sensitivity; "
                    "Pair B: GPT's heatmap is the most sophisticated single "
                    "response; etc.) marking them as provisional and "
                    "specific to this exact model pairing/single run -- not "
                    "general claims about 'Claude' or 'GPT' as model "
                    "classes. This should not be portable into any future "
                    "cumulative synthesis text until Gemini is included and "
                    "multiple runs are completed.\n\n"
                    "3. Revise the form-prediction probe proposal for "
                    "Sprint 7. Ingrid's flaw: confabulated reasoning that is "
                    "internally consistent and structurally specific could "
                    "also allow above-chance form prediction by a blind "
                    "judge -- not because the reasoning caused the form "
                    "choice, but because it accurately describes the form's "
                    "properties after the fact. The contrapositive Naledi "
                    "originally relied on ('if post-hoc, reasoning will be "
                    "too generic to predict from') doesn't hold. Replace/"
                    "extend the probe with Ingrid's better design: "
                    "adversarial pairs where (a) the canonical form for the "
                    "content is known/obvious, and (b) the audience/goal "
                    "variables clearly call for a non-canonical choice. If "
                    "models choose the non-canonical form AND the reasoning "
                    "specifically invokes audience/goal over content "
                    "convention, that is stronger evidence for principled "
                    "reasoning than the prediction probe alone -- because it "
                    "tests whether reasoning actually overrides a strong "
                    "prior, not just whether it's specific. Connect this "
                    "explicitly to point 6 in your original follow-up "
                    "requirements (adversarial pairs), which you had left "
                    "disconnected from the probe design.\n\n"
                    "Keep everything else as-is, including the WHAT THE "
                    "EVIDENCE SHOWS / WHAT THIS MIGHT IMPLY structure, the "
                    "Gemini exclusion flag, and the appendix of raw "
                    "responses. Ingrid also noted two minor interpretive-"
                    "language leaks into the evidence section (the word "
                    "'genuine' re: Claude's reasoning, and the framing of "
                    "GPT's A2 gap as failing to 'interrogate' rather than a "
                    "more precise 'medium-frame anchoring' diagnosis) -- "
                    "tighten both while you're in there, using her more "
                    "precise 'medium-frame anchoring' framing for the GPT-A2 "
                    "case. Output the complete revised brief."
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    revised = response.content[0].text
    db.log_usage("naledi", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"behavioral-reasoning-test-revised-task-{task_id}",
        text=revised,
        metadata={"agent": "naledi", "type": "behavioral_reasoning_test_revised"},
    )
    db.set_memory("naledi", "behavioral_reasoning_test", revised)
    db.update_task(
        task_id, status="completed",
        result="Revision applied; see naledi/behavioral_reasoning_test.",
        artifact_type="research_brief",
        artifact_payload={"memory_key": "naledi/behavioral_reasoning_test"},
    )

    print(f"[{NAME}] Revised behavioral reasoning test:\n\n{revised}")


if __name__ == "__main__":
    run()
