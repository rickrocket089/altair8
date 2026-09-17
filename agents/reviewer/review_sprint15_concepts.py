"""Sprint 15: Ingrid's review gate on Priya's 4 concepts + Kenji's
reality check, per Sophie's process design. Checks (a) are the 4
concepts genuinely diverse or variations on one idea in different
words, (b) are the stated failure modes honest (not softened to look
better), (c) DP2 (model-agnostic) / DP4 (not deck-bound) compliance.
Does not select a winner -- that is the founder's call.
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

    concepts = db.get_memory("priya", "sprint15_concepts") or ""
    reality_check = db.get_memory("kenji", "sprint15_reality_check") or ""
    if not concepts or not reality_check:
        raise SystemExit("Missing priya/sprint15_concepts or kenji/sprint15_reality_check.")

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Sprint 15: review gate on the 4 knowledge-layer concepts",
        description="Diversity, honesty, DP2/DP4 compliance -- not concept selection.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=6000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Review gate on Priya's 4 Sprint 15 concepts (ACFR, FGE, "
            "AAEB, CCO), informed by Kenji's reality check. You do NOT "
            "select a winner or rank the concepts by merit -- that is "
            "the founder's decision. Your job is process integrity.\n\n"
            "CHECK 1 -- GENUINE DIVERSITY. Are these 4 concepts "
            "mechanistically distinct, or do some of them reduce to the "
            "same underlying idea in different vocabulary? Specifically "
            "examine: ACFR (aggregate ranked form-lists per triple) vs. "
            "AAEB (individual annotated exemplars) -- Priya frames these "
            "as different grain, not different mechanism. Is that "
            "distinction real and load-bearing, or is AAEB just ACFR "
            "with richer records? Give a direct verdict.\n\n"
            "CHECK 2 -- HONEST FAILURE MODES. For each concept, is the "
            "stated risk section genuinely the worst honest assessment, "
            "or is it softened? Kenji's reality check flagged that "
            "CCO's claim to have 'the strongest answer' to the binding "
            "objection doesn't hold for its audience-claim edges "
            "specifically -- check whether Priya's own Section 8 already "
            "disclosed this limitation clearly enough, or whether her "
            "framing in Section 6 oversold it before Section 8 walked it "
            "back. Do the same check for any other concept where a "
            "strong claim early in the write-up is quietly qualified "
            "later.\n\n"
            "CHECK 3 -- DP2 (model-agnostic) / DP4 (not deck-bound) "
            "COMPLIANCE. Does any concept implicitly assume a specific "
            "model's capability (e.g. reliable structured output, "
            "reliable claim identification) in a way that would break "
            "DP2 if that assumption doesn't hold across models? Flag "
            "specifically which concept is most model-capability-"
            "dependent and why.\n\n"
            "CHECK 4 -- KENJI'S CROSS-CUTTING FINDING. Kenji found that "
            "the 4 concepts diagnose the 53.9% FVBS failure via 4 "
            "different, largely mutually-exclusive mechanisms (candidate-"
            "set composition / vocabulary gap / reasoning-elicitation / "
            "claim-identification), and Sprint 14's evidence doesn't "
            "discriminate between them. He explicitly declined to "
            "resolve whether Sophie should run a diagnostic test first "
            "or proceed via each concept's own falsifier. Do you agree "
            "this is genuinely unresolved by the evidence, or is there "
            "a way to make progress on it now, from what's already "
            "known, without a new experiment? If you see a way, say so "
            "concretely; if not, confirm it's a real open question for "
            "the founder.\n\n"
            "CHECK 5 -- ANYTHING KENJI MISSED. Kenji's reality check is "
            "thorough but he explicitly avoided ranking. Is there any "
            "concept where his grounding check itself understates a "
            "problem (i.e. he was too generous), or any concept he was "
            "too harsh on relative to the actual evidence?\n\n"
            "GATE VERDICT: are all 4 concepts fit to go forward to the "
            "founder's selection, or does any need revision first (name "
            "exactly what)?\n\n"
            f"=== PRIYA'S 4 CONCEPTS (FULL) ===\n{concepts}\n\n"
            f"=== KENJI'S REALITY CHECK (FULL) ===\n{reality_check}\n"
        )}],
    )

    review = result.text
    db.log_usage("ingrid", result.input_tokens, result.output_tokens)

    db.set_memory("ingrid", "sprint15_concepts_review", review)
    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"sprint15-concepts-review-task-{task_id}",
        text=review,
        metadata={"agent": "ingrid", "type": "sprint15_concepts_review"},
    )
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/sprint15_concepts_review"},
    )

    print(f"[{NAME}] (continuations: {result.continuations})\n\n{review}")
    print(f"\n\n--- {len(review)} chars, stored as ingrid/sprint15_concepts_review ---")


if __name__ == "__main__":
    run()
