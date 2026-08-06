"""Applies Ingrid's 5 documentation/framing corrections to the Sprint 7
adversarial-pairs brief. Same revise-in-place pattern as every prior sprint
revision -- text/framing corrections, no new data collection needed.
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
    original = db.get_memory("naledi", "adversarial_pairs_test") or ""
    review = db.get_memory("ingrid", "sprint7_adversarial_pairs_review") or ""

    if not original or not review:
        raise RuntimeError("Missing original brief or Ingrid's review -- run those first.")

    db.set_memory("naledi", "adversarial_pairs_test_v1", original)

    task_id = db.create_task(
        created_by="ingrid",
        assigned_to="naledi",
        title="Revise Sprint 7 adversarial-pairs brief per Ingrid's review",
        description="Apply Ingrid's 5 documentation/framing corrections.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Your original brief:\n\n{original}\n\n"
                    f"Ingrid's full review:\n\n{review}\n\n"
                    "Apply her 5 corrections specifically -- this is a "
                    "targeted revision, not new research or new data "
                    "collection:\n\n"
                    "1. AP2 canonical-form specification gap: add an "
                    "explicit note that 'bar chart' was too narrow a "
                    "canonical designation for a 6-agent distribution "
                    "comparison -- GPT's box-plot choice in the normal "
                    "variant is evidence of this. Document it as a known "
                    "limitation specific to AP2, and note the corrected "
                    "canonical framing would be 'ranked multi-agent "
                    "comparison visualization' (bar chart being the most "
                    "common instance, not the only defensible one).\n\n"
                    "2. AP1-GPT partial score: the raw GPT response contains "
                    "the sentence 'A full 12-month line chart or table would "
                    "be slower to interpret and would dilute the act now "
                    "message' -- a statement about the canonical form's "
                    "failure that your original scoring narrative didn't "
                    "acknowledge. Engage that sentence directly in the AP1 "
                    "section and explain why it still falls short of the "
                    "explicit-naming bar (it gestures at the form failing "
                    "without naming the specific audience/goal mechanism "
                    "causally).\n\n"
                    "3. Reposition the culturally-scripted-scenario problem: "
                    "currently framed as 'a fair caveat for future rounds' "
                    "-- Ingrid is right that this undersells it. Make clear "
                    "it's an ACTIVE limitation on what the current YES/YES "
                    "scores can mean, especially for AP3/AP4 (highly "
                    "scripted professional scenarios: finance audit, VP "
                    "status check) versus AP5/AP6 (less scripted, more "
                    "diagnostic: medium-rendering constraint, semiotic "
                    "register mismatch). State explicitly that AP5/AP6's "
                    "clean sweeps are better evidence than AP3/AP4's.\n\n"
                    "4. Gemini replication framing: replace 'partially "
                    "replicates' with more precise language -- the Sprint 6 "
                    "form-conservatism pattern did NOT strongly persist "
                    "under adversarial pressure; there is selective "
                    "weakness concentrated in AP1/AP2 whose underlying "
                    "mechanism is unclear from this sample. Don't imply a "
                    "coherent thread that isn't there.\n\n"
                    "5. Apply the one-run-per-variant uncertainty caveat "
                    "symmetrically -- currently it's only applied to the "
                    "strong/clean-sweep results ('did we happen to catch a "
                    "good run?'). The partial/marginal scores (GPT-AP1, "
                    "Gemini-AP2) are equally subject to this -- they could "
                    "be one-run artifacts in either direction.\n\n"
                    "Keep everything else as-is: the overall structure, the "
                    "pair-by-pair evidence sections not mentioned above, the "
                    "two direct-answer sections' bottom-line conclusions "
                    "(Ingrid confirmed these stay within what the data "
                    "supports), and the full raw-response appendix. Output "
                    "the complete revised brief."
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    revised = response.content[0].text
    db.log_usage("naledi", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"adversarial-pairs-test-revised-task-{task_id}",
        text=revised,
        metadata={"agent": "naledi", "type": "adversarial_pairs_test_revised"},
    )
    db.set_memory("naledi", "adversarial_pairs_test", revised)
    db.update_task(
        task_id, status="completed",
        result="Revision applied; see naledi/adversarial_pairs_test.",
        artifact_type="research_brief",
        artifact_payload={"memory_key": "naledi/adversarial_pairs_test"},
    )

    print(f"[{NAME}] Revised adversarial-pairs brief:\n\n{revised}")


if __name__ == "__main__":
    run()
