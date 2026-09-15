"""Ingrid attacks the eight hypotheses with one question: which can exclude nothing?

The founder stated three hypotheses on 2026-09-15 to anchor a path analysis
before the paths are described. Sophie split one of them in two, because it
bundled a proven claim about model weaknesses with an unproven claim about
model knowledge, and carried "we proved this" on both halves. The record
proves one half and points the other way on the other.

That is exactly the failure mode this audit exists to catch, one level up: a
hypothesis written so that no evidence could ever contradict it, or written so
that it silently imports something already assumed.

Sprint 10 failed its own success criterion (b) and Ingrid's verdict was that
the criterion was badly written rather than the work bad. Design principle 4
has the same defect today and nobody has ever been able to fail a path against
it. These hypotheses will anchor a set of design criteria, which will in turn
decide which product paths survive. If they cannot exclude anything, everything
downstream is decoration.

She gets the full record to check against, unsliced.
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

    hypotheses = db.get_memory("team_leader", "hypotheses") or "(missing)"
    principles = db.get_memory("team_leader", "design_principles") or "(missing)"
    north_star = db.get_memory("team_leader", "north_star") or "(missing)"

    sprints = db.list_sprints()
    outcomes = "\n\n".join(
        f"--- Sprint {s['sprint_number']} ---\nQUESTION: {s['question']}\n\nOUTCOME: {s['outcome']}"
        for s in sorted(sprints, key=lambda s: s["sprint_number"])
        if s["status"] == "completed"
    )
    approaches = "\n\n".join(
        f"--- #{a['id']} [{a['category']}] {a['title']} ---\n{a['description']}"
        for a in db.list_candidate_approaches()
    )

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Audit: the eight hypotheses, before they anchor design criteria",
        description="One question -- which of these can exclude nothing?",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "The founder is about to change the programme's direction: from a "
            "research cadence toward analysing concrete paths to a product -- "
            "software that replaces the deck. Before the paths are described, "
            "he wants the assumptions fixed, so that criteria cannot be "
            "retrofitted to whichever path is already the favourite.\n\n"
            "He stated three hypotheses. Sophie split the first into two and "
            "reclassified the browser one as an assumption, and wrote all of "
            "them into the record with an explicit evidence status each. The "
            "result is hypotheses 5 to 8 below, alongside the original 1 to 4.\n\n"
            "YOUR TASK IS ONE QUESTION, asked of every one of the eight:\n\n"
            "**WHICH OF THESE CAN EXCLUDE NOTHING?**\n\n"
            "For each hypothesis, state what observation would falsify it. If "
            "you cannot name one, the hypothesis is decoration and you should "
            "say so and propose either a formulation that can fail or its "
            "removal. Design principle 4 is the standing example of this "
            "defect in the team's own record -- a value nobody can fail a path "
            "against -- and Sprint 10's criterion (b) is the standing example "
            "of what it costs.\n\n"
            "Then four specific things:\n\n"
            "1. HYPOTHESIS 6 IS THE LOAD-BEARING ONE. The founder originally "
            "wrote the opposite of it -- that models hold NO knowledge of the "
            "relationship between visualization, audience and content, and "
            "that this was proven. Sophie reversed it to 'latent but "
            "unreliable' on the strength of Sprints 6 and 7, which you audited "
            "this morning and downgraded to directional evidence from two "
            "small pilots with an uncompensated validity threat. So: is 'latent "
            "but unreliable' itself an overclaim in the other direction? What "
            "is the most honest formulation that neither asserts the knowledge "
            "is there nor that it is absent, and can still do useful work as "
            "an anchor for design criteria? Be precise -- this sentence will "
            "decide an architecture.\n\n"
            "2. THE SPLIT ITSELF. Sophie separated a claim about MODELS "
            "(hypothesis 6) from a claim about SYSTEMS (hypothesis 7) and "
            "noted they are routinely confused. Is that a real distinction "
            "doing real work, or is she manufacturing precision? Does anything "
            "in the record actually turn on it?\n\n"
            "3. HYPOTHESIS 8 AS AN ASSUMPTION. She argues the browser "
            "assumption 'cannot be false, only expensive', and separates the "
            "substrate's expressive ceiling from the agent's reliable "
            "generation ceiling -- your own Sprint 9 methodological point. Is "
            "reclassifying it from hypothesis to assumption legitimate, or is "
            "it a way of protecting a decision from falsification? What would "
            "have to be true for the browser assumption to be WRONG rather "
            "than merely costly?\n\n"
            "4. WHAT IS MISSING. An assumption this programme is running on "
            "that appears nowhere in the eight. Look for the ones nobody "
            "states because everyone shares them -- for instance whether a "
            "single artifact is even the right unit of business communication, "
            "or whether the person who commissions a deck and the person who "
            "reads it want the same thing. Name at most three, and for each "
            "say what it would cost to have it wrong.\n\n"
            "Also on the record, for context rather than judgement: the "
            "founder has re-proposed building a knowledge structure from "
            "existing business-communication corpora (slidemodel.com and "
            "similar) as a route to hypothesis 6. He raised a version of this "
            "in August; Sophie advised against it and it became Sprint 9 "
            "instead. It is logged as candidate approach #11 with the "
            "objection attached. You are not being asked to rule on it here -- "
            "but if it bears on how hypothesis 6 should be worded, say so.\n\n"
            "Write for the founder. He is making a direction decision on top "
            "of these sentences.\n\n"
            f"=== THE EIGHT HYPOTHESES ===\n{hypotheses}\n\n"
            f"=== DESIGN PRINCIPLES ===\n{principles}\n\n"
            f"=== NORTH STAR ===\n{north_star}\n\n"
            f"=== ALL SPRINT OUTCOMES ===\n{outcomes}\n\n"
            f"=== CANDIDATE APPROACHES ===\n{approaches}\n"
        )}],
    ) as stream:
        response = stream.get_final_message()

    audit = response.content[0].text
    db.log_usage("ingrid", response.usage.input_tokens, response.usage.output_tokens)

    db.set_memory("ingrid", "hypotheses_audit", audit)
    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"review-task-{task_id}",
        text=audit,
        metadata={"agent": "ingrid", "type": "hypotheses_audit"},
    )
    db.update_task(
        task_id, status="completed", result=audit,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/hypotheses_audit"},
    )

    print(f"[{NAME}]\n\n{audit}")
    print(f"\n\n--- {len(audit)} chars, stored as ingrid/hypotheses_audit ---")


if __name__ == "__main__":
    run()
