"""Entry point for Ingrid to critically review Sprint 6: Naledi's behavioral
reasoning test (principled vs. confabulated visual-form selection),
answering Ingrid's own open question from Sprint 4.
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
        title="Review: Sprint 6 (behavioral reasoning test)",
        description="Critically review Naledi's principled-vs-confabulated pilot before the sprint closes.",
    )

    brief = db.get_memory("naledi", "behavioral_reasoning_test") or "(no brief found)"

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "This is your own open question from Sprint 4, now "
                    "answered by Naledi with a real (if small) behavioral "
                    "experiment. Review it with the same rigor you'd apply "
                    "to anyone else's work -- being the one who asked the "
                    "question doesn't earn it a pass.\n\n"
                    f"{brief}\n\n"
                    "Specific things to scrutinize:\n\n"
                    "1. Naledi rated the reasoning quality herself, fully "
                    "aware of which model produced which response -- she "
                    "flags this as a bias risk herself. Does that self-flag "
                    "hold up, or does her prose show detectable bias toward "
                    "one model (e.g. does she credit Claude's reasoning more "
                    "generously than GPT's for comparable quality)?\n\n"
                    "2. Check the evidence/implication split (S6 from "
                    "Sprint Review #1) -- is it actually maintained "
                    "throughout, or does interpretation leak into the "
                    "'WHAT THE EVIDENCE SHOWS' section?\n\n"
                    "3. Is the 60/40 confidence estimate ('principled' vs "
                    "'inconclusive') actually grounded in anything "
                    "systematic, or is it an intuitive number dressed up "
                    "with false precision? A stated percentage on 6 data "
                    "points deserves scrutiny.\n\n"
                    "4. The GPT-A2 case is used as the strongest evidence "
                    "for confabulation/form-prior-override. Read the actual "
                    "quoted GPT reasoning in the appendix -- is that "
                    "characterization fair, or does it slightly overstate "
                    "how bad GPT's answer actually was?\n\n"
                    "5. Naledi proposes a 'form-prediction probe' as the "
                    "decisive follow-up experiment. Is that actually a good "
                    "test design, or does it have its own flaws (e.g. could "
                    "a blind judge predict the form from reasoning that is "
                    "itself confabulated but internally consistent, making "
                    "the probe pass even when the reasoning wasn't causally "
                    "real)?\n\n"
                    "6. Is the Gemini-exclusion flag (made prominently, "
                    "top of the brief) sufficient, or does the brief's "
                    "final verdict implicitly generalize beyond what a "
                    "2-model dataset supports?\n\n"
                    "End with a recommendation: proceed, revise, or block. "
                    "Then state plainly whether this pilot is sufficient to "
                    "hand to Sophie as informing (not deciding) the "
                    "founder's solution-direction choice, or whether it "
                    "needs revision before even that limited use."
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
        metadata={"agent": "ingrid", "type": "sprint6_review"},
    )
    db.set_memory("ingrid", "sprint6_review", review)
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review", artifact_payload={"memory_key": "ingrid/sprint6_review"},
    )

    print(f"[{NAME}]\n\n{review}")


if __name__ == "__main__":
    run()
