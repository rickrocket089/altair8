"""Priya restates the novelty claims for the three Category B concepts.

Kenji's verification put C1, C2 and C5 in Category B: viable concepts whose
stated novelty claim is too broad for the evidence. He specified what each
restatement must acknowledge and what the surviving claim actually is.

Priya does the restatement because they are her concepts and field 3 is her
claim to make. She is not re-verifying anything -- the verdict is Kenji's and
is not up for negotiation here. Her permissions still exclude web_search, so
she cannot check her own prior art, which is the point.

The failure mode this is watched for: restating a claim while quietly
re-broadening it. A restatement that acknowledges PaperTrail and then asserts
the original sweeping claim anyway is worse than no restatement, because it
looks like the correction was made.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.concept_designer.persona import NAME, SYSTEM_PROMPT
from agents.permissions import require_tool
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"


def run() -> None:
    require_tool("priya", "write_concept_scenario")
    db.set_memory("priya", "status", "online")

    blind = db.get_memory("priya", "sprint10_concepts_blind") or "(missing)"
    verification = db.get_memory("kenji", "sprint10_concept_verification") or "(missing)"

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="priya",
        title="Sprint 10: restate the three Category B novelty claims",
        description="C1, C2, C5 -- narrow the claim to what Kenji's evidence supports.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model=MODEL,
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Kenji has verified your six concepts against real retrieved "
            "literature. Three of yours -- C1 (Commitment Audit), C2 "
            "(Audience-in-the-Loop Simulation) and C5 (Relational Register "
            "Adaptation) -- are Category B: the concept is viable, but the "
            "novelty claim as you wrote it is broader than the evidence "
            "supports. Rewrite field 3 for each.\n\n"
            "Terms of this task:\n\n"
            "1. The verdict is not up for negotiation. You have no web_search "
            "and cannot check prior art yourself; that is deliberate. If you "
            "think Kenji has misread a concept, say so in a separate note at "
            "the end -- do not encode the disagreement in the restatement.\n\n"
            "2. Name the prior art explicitly, in the claim itself. A reader "
            "who sees only your field 3 must learn that PaperTrail, "
            "PosterMate, Proxona or the register-synthesis literature exists. "
            "Do not relegate it to a caveat at the end.\n\n"
            "3. State only what survives. The restatement must be narrower "
            "than the original, and a reader should be able to check it "
            "against Kenji's evidence and agree.\n\n"
            "4. THE FAILURE MODE I AM WATCHING FOR: acknowledging the prior "
            "art and then asserting the original sweeping claim anyway. That "
            "is worse than not restating at all, because it looks like the "
            "correction was made. If what survives is thin, write that it is "
            "thin.\n\n"
            "5. Where Kenji flagged that a literature was NOT reached -- the "
            "politeness-theory computational work for C5, the older NLG "
            "planning literature for C2 -- your restatement must carry that "
            "as an open question, not omit it. An unverified claim presented "
            "as verified is the specific thing this whole sprint was built to "
            "avoid.\n\n"
            "Kenji's proposed restatements are in his brief. You may adopt "
            "his wording, sharpen it, or write your own -- but you may not "
            "make the claim broader than his.\n\n"
            "=========== YOUR ORIGINAL CONCEPTS ===========\n"
            f"{blind}\n\n"
            "=========== KENJI'S VERIFICATION ===========\n"
            f"{verification}\n\n"
            "=========== PRODUCE ===========\n"
            "For each of C1, C2 and C5:\n"
            "  - the concept name\n"
            "  - ORIGINAL CLAIM: quote your own field 3 in one sentence\n"
            "  - PRIOR ART ACKNOWLEDGED: named, specific\n"
            "  - RESTATED CLAIM: the replacement field 3, written to be "
            "dropped into the concept as-is\n"
            "  - WHAT THIS GIVES UP: what you can no longer say, plainly\n"
            "  - STILL UNVERIFIED: any literature Kenji could not reach that "
            "bears on this claim, or 'none'\n\n"
            "Then a short closing section: across all three, did the "
            "verification leave you with less than you thought you had? "
            "Answer honestly. Do not be gracious about it if the answer is yes."
        )}],
    ) as stream:
        response = stream.get_final_message()

    restated = response.content[0].text
    db.log_usage("priya", response.usage.input_tokens, response.usage.output_tokens)

    db.set_memory("priya", "sprint10_restated_claims", restated)
    vectorstore.remember(
        collection_name="concept_designer_memory",
        doc_id=f"sprint10-restated-task-{task_id}",
        text=restated,
        metadata={"agent": "priya", "type": "restated_claims", "sprint": 10},
    )
    db.update_task(
        task_id, status="completed", result=restated,
        artifact_type="restated_claims",
        artifact_payload={"memory_key": "priya/sprint10_restated_claims",
                          "concepts": ["C1", "C2", "C5"]},
    )

    # Cheap inspection: did the required prior art actually get named?
    required = {
        "C1": ["PaperTrail"],
        "C2": ["PosterMate", "Proxona"],
        "C5": ["register"],
    }
    print(f"\n[{NAME}] Inspection — required prior art named in the text:")
    for concept, names in required.items():
        for n in names:
            print(f"    {concept}: '{n}' present: {n.lower() in restated.lower()}")

    print(f"\n[{NAME}]\n\n{restated}")


if __name__ == "__main__":
    run()
