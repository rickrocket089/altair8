"""Entry point for the Reviewer agent (Dr. Ingrid Solberg).

Reads everyone else's outputs from Postgres and produces a critical review
with an explicit recommendation for Sophie.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))


def run() -> None:
    db.set_memory("ingrid", "status", "online")
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Review: Week 1 research + prototype outputs",
        description="Critically review Kenji's, Naledi's, and Mateo's outputs; recommend next step to Sophie.",
    )

    kenji_brief = db.get_memory("kenji", "last_brief") or "(no prior brief found)"
    naledi_brief = db.get_memory("naledi", "last_brief") or "(no prior brief found)"
    mateo_explanation = db.get_memory("mateo", "last_explanation") or "(no prior explanation found)"

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Kenji's literature brief:\n\n{kenji_brief}\n\n"
                    f"Naledi's cognitive-science brief:\n\n{naledi_brief}\n\n"
                    f"Mateo's prototype explanation:\n\n{mateo_explanation}\n\n"
                    "Critically review all three outputs. Check claims against cited "
                    "evidence, flag overclaims or gaps, assess whether Mateo's prototype "
                    "genuinely follows from the research. End with a clear recommendation "
                    "to Sophie: proceed, revise, or block — and why."
                ),
            }
        ],
    )
    review = response.content[0].text
    db.log_usage("ingrid", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"review-task-{task_id}",
        text=review,
        metadata={"agent": "ingrid", "type": "review"},
    )
    db.set_memory("ingrid", "last_review", review)
    db.update_task(task_id, status="completed", result=review)

    print(f"[{NAME}]\n\n{review}")


if __name__ == "__main__":
    run()
