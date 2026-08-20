"""Ingrid checks Pass 4's marks. The only external check Pass 4 has.

Agreed as a pre-opening action after she found Pass 4 had no verification step
at all (New Problem A): Passes 1-3 each have an external check, and the
synthesis -- historically where this team's output drifts from observation into
prescription -- had none.

Deliberately narrow by design: she reviews whether the marking is HONEST, not
the whole synthesis. Two failure directions matter and she is asked about both:
  - unmarked sentences that have no referent in Passes 1-3 (a claim smuggled in
    as a finding), which is the dangerous direction;
  - marked sentences that do have referents (marker used as decoration), which
    devalues the mark until it means nothing.

Keeping this cheap is the point. A full review of the synthesis would make the
check a bottleneck and it would stop being run.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")

    synthesis = db.get_memory("team_leader", "sprint10_synthesis") or "(missing)"
    blind = db.get_memory("priya", "sprint10_concepts_blind") or ""
    sighted = db.get_memory("priya", "sprint10_concepts_sighted") or ""
    verification = db.get_memory("kenji", "sprint10_concept_verification") or ""
    buildability = db.get_memory("mateo", "sprint10_buildability") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Check Sprint 10 Pass 4 marking honesty",
        description="Narrow check: are Sophie's own observations marked, and only those?",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=10000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "This is the narrow check you specified as New Problem A in your "
            "Sprint 10 confirmation review. You are NOT reviewing the whole "
            "synthesis -- deliberately, so this check stays cheap enough to "
            "actually get run. You are checking whether the marking is "
            "honest.\n\n"
            "The rule Sophie was given: any sentence in the comparison "
            "sections without a direct referent in Pass 1, 2 or 3 must begin "
            "with [SOPHIE]. Marked sentences are her own observations, not "
            "sprint findings.\n\n"
            "Check both failure directions:\n\n"
            "1. UNMARKED SENTENCES THAT SHOULD BE MARKED. This is the "
            "dangerous direction -- an observation of Sophie's presented as "
            "something the sprint found. Quote every instance you find. Pay "
            "particular attention to Section 3, which is written as plain "
            "fact and would be the easiest place to smuggle in a "
            "characterisation nobody actually made.\n\n"
            "2. MARKED SENTENCES THAT DO HAVE REFERENTS. Marker used as "
            "decoration. Less dangerous but it devalues the mark until it "
            "means nothing, which destroys the mechanism.\n\n"
            "3. Did Sophie obey the no-new-claims constraint elsewhere -- "
            "specifically, did she resolve any disagreement between agents by "
            "picking a side, rather than showing the disagreement? And did she "
            "recommend a winner, which she was told not to do?\n\n"
            "4. Section 3 was supposed to state plainly what the sprint did "
            "NOT establish. Does it actually do that, or does it soften? "
            "Check specifically that it says no concept reached your Category "
            "A, and that it does not present Kenji's verdicts as more settled "
            "than his own retrieval logs support.\n\n"
            "=========== PASS 4 SYNTHESIS ===========\n"
            f"{synthesis}\n\n"
            "=========== SOURCE: PASS 1 ===========\n"
            f"{blind[:30000]}\n\n"
            "=========== SOURCE: PASS 2 ===========\n"
            f"{sighted[:25000]}\n\n"
            "=========== SOURCE: PASS 3 ===========\n"
            f"{verification[:30000]}\n\n"
            "=========== SOURCE: MATEO ===========\n"
            f"{buildability}\n\n"
            "End with: MARKING HONEST — synthesis may go to the founder, or "
            "MARKING NOT HONEST — with the specific sentences that must be "
            "marked or unmarked first."
        )}],
    ) as stream:
        response = stream.get_final_message()

    review = response.content[0].text
    db.log_usage("ingrid", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"review-task-{task_id}",
        text=review,
        metadata={"agent": "ingrid", "type": "sprint10_synthesis_mark_check"},
    )
    db.set_memory("ingrid", "sprint10_synthesis_mark_check", review)
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/sprint10_synthesis_mark_check"},
    )

    print(f"[{NAME}]\n\n{review}")


if __name__ == "__main__":
    run()
