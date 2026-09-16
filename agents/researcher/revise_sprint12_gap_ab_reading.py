"""Kenji applies Ingrid's three required Sprint 12 revisions.

Targeted text revision, not new research -- same practice as every prior
revision in this project.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))


def run() -> None:
    require_tool("kenji", "write_brief")
    original = db.get_memory("kenji", "sprint12_gap_ab_reading") or ""
    review = db.get_memory("ingrid", "sprint12_gap_ab_review") or ""

    if not original or not review:
        raise RuntimeError("Missing original brief or Ingrid's review -- run those first.")

    db.set_memory("kenji", "sprint12_gap_ab_reading_v1", original)

    task_id = db.create_task(
        created_by="ingrid",
        assigned_to="kenji",
        title="Revise Sprint 12 synthesis per Ingrid's review",
        description="Apply her three required corrections -- targeted text fix, not new research.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=10000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            f"Your original brief:\n\n{original}\n\n"
            f"Ingrid's full review:\n\n{review}\n\n"
            "Apply her three REQUIRED corrections. Targeted text revision, "
            "no new reading or research:\n\n"
            "1. (Required) Revise the Bangalore & Stent and "
            "Danescu-Niculescu-Mizil et al. per-paper readings. Both "
            "currently say the finding is 'equally consistent with both "
            "accounts.' Ingrid's correction: both are actually "
            "asymmetrically consistent -- weak directional pressure AGAINST "
            "simple convention-reproduction, not full equipoise. For "
            "Bangalore & Stent: near-chance cross-user transfer "
            "(RankLoss<=0.52 vs 0.50 baseline) is weak disconfirming "
            "evidence for pure convention-reproduction, since that account "
            "predicts better-than-chance transfer of shared conventions "
            "across users. For Danescu et al.: cross-domain classifier "
            "generalization is harder to explain under narrow convention-"
            "reproduction (which would predict community-specific, non-"
            "transferring patterns) than Ingrid's note acknowledges -- "
            "though a shared-training-data confound means this isn't "
            "conclusive either. Revise both H6 RELEVANCE lines to state "
            "this asymmetry plainly. The null-result conclusion (neither "
            "paper discriminates the accounts) does NOT change -- only the "
            "characterization of what non-discriminating evidence still "
            "leans toward.\n\n"
            "2. (Required) Fix the criterion (b) framing in Section 4. You "
            "currently propose that Sophie 'should update the criterion to "
            "reflect' that direction means 'run the test.' Ingrid's finding: "
            "this is you deciding Sophie's own closure criterion for her, "
            "not correctly flagging a decision point. Replace it with a "
            "clean, neutral presentation of BOTH possible readings of "
            "criterion (b) -- (i) it requires a theoretical/directional lean "
            "from the literature toward one explanation, which this null "
            "result cannot supply, or (ii) it is satisfied by a clear "
            "methodological direction for resolution, which the null result "
            "does supply ('the test must be behavioral, literature can't "
            "settle it') -- and explicitly hand the decision to Sophie "
            "rather than recommending which reading she should adopt.\n\n"
            "3. (Required) Fix the Danescu citation in the Backlog #23 "
            "design-note (Section 5). Currently both Bangalore & Stent and "
            "Danescu are cited together to support a 'novel-context "
            "conditions' recommendation. Ingrid's correction: only "
            "Bangalore & Stent genuinely supports novel-context conditions "
            "(idiosyncratic preferences mean familiar-task testing risks "
            "conflating individual convention-acquisition with internalized "
            "structure). Danescu's sentence-position finding actually "
            "supports a DIFFERENT design point -- that #23's measurement "
            "instrument should be sensitive to compositional/positional "
            "effects within items, not that the test needs a novel-context "
            "manipulation. Separate these into two distinct, correctly-"
            "attributed design notes rather than one merged citation.\n\n"
            "LOWER PRIORITY (also apply): in the NOVELTY FLAG discussion for "
            "van Gelder (appears in the per-paper reading AND in Section 2 "
            "of the synthesis), replace 'categorically different' with "
            "language reflecting Ingrid's finding: the mechanisms differ on "
            "two specific dimensions (what the scalar represents; whether "
            "it's bound to an epistemic category before driving visual "
            "weight) but are structurally adjacent enough on the scalar-to-"
            "visual-salience dimension to warrant a formalization "
            "comparison if C1's mechanism is ever specified in full detail. "
            "This does NOT become a novelty flag -- van Gelder's paper does "
            "not show C1's specific mechanism already existing -- just more "
            "honest language about how close it is.\n\n"
            "Leave everything else -- all other per-paper readings, the "
            "direct-answer conclusion, the 'one thing worth keeping' table, "
            "the recommendation to run Backlog #23 -- exactly as it was; "
            "Ingrid confirmed those parts are sound. Output the complete "
            "revised brief (synthesis + per-paper readings, same structure "
            "as the original)."
        )}],
    ) as stream:
        resp = stream.get_final_message()

    revised = resp.content[0].text
    db.log_usage("kenji", resp.usage.input_tokens, resp.usage.output_tokens)

    db.set_memory("kenji", "sprint12_gap_ab_reading", revised)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"sprint12-reading-revised-task-{task_id}",
        text=revised,
        metadata={"agent": "kenji", "type": "sprint12_gap_ab_reading_revised"},
    )
    db.update_task(
        task_id, status="completed", result=revised,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/sprint12_gap_ab_reading"},
    )

    print(f"[{NAME}] Revised Sprint 12 brief:\n\n{revised}")
    print(f"\n\n--- {len(revised)} chars, stored as kenji/sprint12_gap_ab_reading (v1 preserved) ---")


if __name__ == "__main__":
    run()
