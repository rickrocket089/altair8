"""Kenji reads the one paper he refused to clear C1 against from an abstract.

His re-verification brief named it as the single highest-priority item: the
mechanism that would decide whether C1's claim survives lives in the body, and
he would not let an abstract stand in for it. The founder supplied the full
text on 2026-09-15.

Armstrong, Anderson, Planchart, Baidoo & Peterson, "Addressing Uncertainty in
LLM Outputs for Trust Calibration Through Visualization and User Interface
Design", Visible Language, 2025. Open access. 42 pages.

This is the first full-text paper in the project's history. Every prior novelty
verdict in eleven sprints rests on titles and abstracts.

The question is narrow and it matters more than it looks. C1's defensible
position is that visual weight derives from confidence that the AUTHOR assigned
to their own claim, bound to an epistemic category. Armstrong et al. present
eight visual conventions for representing uncertainty in LLM output. If those
conventions derive visual weight from confidence bound to a claim-level
category, C1's position narrows severely -- and Kenji's own note from the
re-verification applies with force: if a model rather than an author assigns the
confidence, the distinction C1 rests on begins to dissolve, which is precisely
what backlog #24 would do to it.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, fulltext, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"
SLUG = "addressing-uncertainty-in-llm-outputs-for-trust-calibration"


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    paper = fulltext.read(SLUG)
    prior = db.get_memory("kenji", "c1_uncertainty_literature_check") or ""
    spec = db.get_memory("mateo", "c1_spanning_scaffold_spec") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Read Armstrong et al. in full and settle C1's novelty verdict",
        description="The paper you named as blocking. Founder supplied the full text.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model=MODEL, max_tokens=16000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "You named this paper as the single item blocking a confirmed "
            "verdict on C1, and refused to clear it from the abstract because "
            "the mechanism lives in the body. The founder has supplied the "
            "full text. It is below, all 42 pages of it.\n\n"
            "This is the first full text this project has ever read. Every "
            "novelty verdict in eleven sprints rested on titles and abstracts. "
            "Use the privilege: cite page-level specifics, quote the mechanism "
            "where it matters, and do not retreat into the kind of general "
            "characterisation an abstract would have supported anyway.\n\n"
            "ANSWER, in this order:\n\n"
            "1. WHAT ARE THE EIGHT VISUAL CONVENTIONS, concretely? For each: "
            "what is encoded, in what visual variable, and at what granularity "
            "-- token, sentence, claim, whole summary?\n\n"
            "2. THE DECIDING QUESTION. Does any convention derive VISUAL "
            "WEIGHT from a CONFIDENCE VALUE bound to an EPISTEMIC CATEGORY of "
            "a claim (evidence / inference / assumption / assertion, or any "
            "equivalent scheme)? Quote the passage that settles it either way. "
            "If they do something adjacent but categorically different -- for "
            "instance encoding token-level model probability rather than "
            "claim-level epistemic status -- say exactly where the line falls, "
            "because that line is C1's entire position.\n\n"
            "3. WHO ASSIGNS THE CONFIDENCE in their system, the model or a "
            "human? You flagged in your own re-verification that if an LLM "
            "assigns the scores in C1, C1's gap against existing work narrows "
            "materially. This paper is the test of that claim: if their "
            "model-assigned uncertainty produces something that looks like "
            "C1's output, then the moment backlog #24 makes our model the "
            "assigner, we arrive where they already are. Address this "
            "directly.\n\n"
            "4. THEIR MAVS SYSTEM AND ITS THREE VIRTUAL AGENTS. Is that an "
            "architecture Altair8 is heading toward without knowing it? Say so "
            "if it is.\n\n"
            "5. WHAT DID THEY VALIDATE, AND HOW? Real readers or designer "
            "judgement? If they ran anything with human participants, describe "
            "the design and the result -- this team has never put an artifact "
            "in front of a reader, and someone else's evaluation of adjacent "
            "material is the closest thing to evidence we have on whether "
            "admitted uncertainty changes anything for the person reading.\n\n"
            "6. THE VERDICT ON C1. Held, narrowed, or fallen. If narrowed, "
            "restate the defensible position as tightly as this paper now "
            "forces. If it has fallen, say that in the first sentence of this "
            "section and do not soften it -- the founder is deciding a product "
            "direction and a comfortable answer is worth nothing.\n\n"
            "7. WHAT THIS PAPER GIVES US THAT IS NOT ABOUT NOVELTY. Findings, "
            "frameworks or failure modes worth keeping regardless of the "
            "verdict.\n\n"
            f"C1'S SCAFFOLD SPEC:\n{spec[:12000]}\n\n"
            f"YOUR OWN RE-VERIFICATION BRIEF:\n{prior}\n\n"
            f"=== FULL TEXT: ARMSTRONG ET AL. 2025 ===\n{paper}\n"
        )}],
    ) as stream:
        resp = stream.get_final_message()

    brief = resp.content[0].text
    db.log_usage("kenji", resp.usage.input_tokens, resp.usage.output_tokens)

    db.set_memory("kenji", "armstrong_fulltext_verdict", brief)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"brief-task-{task_id}",
        text=brief,
        metadata={"agent": "kenji", "type": "armstrong_fulltext_verdict"},
    )
    db.update_task(
        task_id, status="completed", result=brief,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/armstrong_fulltext_verdict"},
    )

    print(f"[{NAME}]\n\n{brief}")
    print(f"\n\n--- {len(brief)} chars, stored as kenji/armstrong_fulltext_verdict ---")


if __name__ == "__main__":
    run()
