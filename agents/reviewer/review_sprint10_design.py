"""Ingrid reviews the Sprint 10 DESIGN before the sprint opens.

Same order as Sprint 8's architecture review: the method gets attacked before
anyone runs it, not after four concept scenarios exist and are expensive to
throw away.

max_tokens is 16000 deliberately. 8000 has now truncated three separate long
reviews in this project (the infrastructure section, the Sprint 6 Gemini
synthesis, sprint_review_2) -- this is a known, repeated failure mode here.
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

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Review: Sprint 10 design (blind-then-sighted concept generation)",
        description="Design review before the sprint opens. No work has been run yet.",
    )

    proposal = db.get_memory("team_leader", "sprint10_proposal") or "(no proposal found)"
    hypotheses = db.get_memory("team_leader", "hypotheses") or ""
    design_principles = db.get_memory("team_leader", "design_principles") or ""

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Review the METHOD, before it is run. Nothing has been "
                    "executed yet -- no concepts exist. This is the same "
                    "review-before-build order used for Sprint 8's "
                    "architecture.\n\n"
                    "Context you need: a sixth agent has been hired, Priya "
                    "Raghunathan, a speculative/critical designer whose role "
                    "is generating and specifying rival concepts. She has no "
                    "web_search in agents/permissions.py by design, so that "
                    "novelty verification stays with Kenji and she cannot "
                    "self-certify her own originality.\n\n"
                    f"THE TEAM'S HYPOTHESES:\n{hypotheses}\n\n"
                    f"THE TEAM'S DESIGN PRINCIPLES:\n{design_principles}\n\n"
                    f"SOPHIE'S SPRINT 10 PROPOSAL:\n\n{proposal}\n\n"
                    "Attack these specifically:\n\n"
                    "1. THE CENTRAL QUESTION. Section 8 concedes that Priya "
                    "cannot be blind to prior art -- her base model read the "
                    "literature in pretraining -- and narrows the claim to "
                    "'does explicit seeding pull the output.' Is that "
                    "narrowed claim actually worth a sprint, or is "
                    "blind-then-sighted procedural theatre that produces a "
                    "difference we cannot interpret? If it is theatre, say "
                    "so plainly and say what should replace it. If it is "
                    "sound, state precisely what a Pass 1 vs Pass 2 "
                    "difference would and would not license us to claim.\n\n"
                    "2. Is the constraint set (section 5) rich enough to "
                    "derive concepts from, or so thin that Pass 1 is "
                    "structurally set up to produce either vagueness or "
                    "recycled prior art? Be concrete about what is missing "
                    "if anything is.\n\n"
                    "3. Field 5 asks Priya to grade her own concept's "
                    "novelty pending Kenji's check. Section 11 asks whether "
                    "novelty is the right target at all. Give a real answer: "
                    "does grading novelty distort concept generation toward "
                    "exotic-but-wrong, and if so what should field 5 become?\n\n"
                    "4. Is the seven-field template rigorous enough to be "
                    "worth filling in? Specifically: does it let a concept "
                    "pass while remaining unbuildable, and is field 6 "
                    "(falsification) doing real work or will it collect "
                    "plausible-sounding tests nobody could actually run? "
                    "Success criterion (b) says Mateo judges buildability -- "
                    "is that check sufficient, and is it placed at the right "
                    "point in the sequence?\n\n"
                    "5. What procedurally verifies Pass 1 was genuinely run "
                    "blind? Right now the answer is 'the orchestrating "
                    "session ran it that way.' Is that adequate given this "
                    "project's own documented history of rules existing "
                    "without enforcement (your Process Review #1 and #2 "
                    "finding), and if not, what concrete check would you "
                    "require?\n\n"
                    "6. Pass 3 says you never see which pass a concept came "
                    "from, to keep Kenji's verification unbiased. Is that "
                    "blinding actually achievable in practice, or will the "
                    "concepts self-identify by content?\n\n"
                    "7. Does this design violate any design principle, "
                    "particularly #4 and its implementation-ease addendum? "
                    "And does deferring Phase C validation AGAIN carry a "
                    "cost the proposal understates -- Sprint 9's public "
                    "results page promises that validation as Sprint 10.\n\n"
                    "8. Anything scoped out that should be in, or in that "
                    "should be cut.\n\n"
                    "Note for your own scope check: you have a standing "
                    "instruction to verify Sophie's stated Process Review "
                    "count independently rather than trust it. Process "
                    "reviews on record: #1 covering sprints 1-5, #2 covering "
                    "sprints 6-9. Sprint 10 would be the first since #2.\n\n"
                    "End with a clear recommendation: proceed as designed, "
                    "revise the design first, or block."
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()

    review = response.content[0].text
    db.log_usage("ingrid", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"review-task-{task_id}",
        text=review,
        metadata={"agent": "ingrid", "type": "sprint10_design_review"},
    )
    db.set_memory("ingrid", "sprint10_design_review", review)
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/sprint10_design_review"},
    )

    print(f"[{NAME}]\n\n{review}")
    print(f"\n\n--- {len(review)} chars "
          f"(check for truncation: does it end with a recommendation?) ---")


if __name__ == "__main__":
    run()
