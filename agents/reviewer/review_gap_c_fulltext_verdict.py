"""Ingrid reviews Kenji's Gap C full-text brief before it counts as settled.

Two real risks specific to this brief, both self-inflicted opportunities for
overclaim: (1) the Munzner source is a confirmed 5-slide talk excerpt, not the
book -- did Kenji actually hold that caveat throughout, or let it slip
anywhere into book-scope claims? (2) the brief draws a real inference chain
from "Mackinlay's formal criteria have no audience parameter" to "a positive
Backlog #23 finding would mean the model's audience-sensitivity came from
somewhere else" -- that chain is doing real interpretive work for a founder
direction decision and deserves the same scrutiny Ingrid gave the hypotheses
audit the day before.
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

    brief = db.get_memory("kenji", "gap_c_fulltext_verdict") or "(missing)"
    hypotheses = db.get_memory("team_leader", "hypotheses") or "(missing)"

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Review: Kenji's Gap C full-text verdict (Mackinlay + Munzner excerpt)",
        description=(
            "Founder asked for this reviewed before it counts as settled. "
            "Content review, not a sprint review."
        ),
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Kenji read two founder-supplied full texts and answered whether "
            "the formal visualization-design tradition models audience, for "
            "candidate approach #11's 'cheaper first' check and as input to "
            "how hypothesis 6 / backlog #23 should be interpreted. Review it "
            "before the founder treats it as settled.\n\n"
            "SPECIFIC THINGS TO CHECK, not a generic pass:\n\n"
            "1. THE MUNZNER CAVEAT, HELD OR LEAKED. The second source is "
            "confirmed to be a 5-slide talk excerpt from Munzner's own site, "
            "not the 2014 book -- Kenji was explicitly instructed to treat "
            "every claim from it as provisional and scoped to five slides. "
            "Read section 2 and section 3 closely: does he actually hold that "
            "line throughout, or does any sentence quietly generalize from "
            "'the excerpt shows X' to something that reads as a claim about "
            "the book's actual content or argument? Quote anywhere the "
            "caveat slips, if it does.\n\n"
            "2. THE MACKINLAY VERDICT, VERIFIED AGAINST WHAT'S QUOTED. He "
            "claims expressiveness/effectiveness take no audience parameter, "
            "with direct quotes from Sections 5, 6, 8. Does the evidence he "
            "quotes actually support the strength of the verdict he draws, or "
            "does the one 'profile of a particular user' passage (Section 8, "
            "p.137) deserve more weight than he gives it -- it IS Mackinlay "
            "naming user-tailoring, even if only as an override mechanism? "
            "Is 'the formal tradition does not model audience' the right "
            "level of confidence, or should it be hedged further given that "
            "one passage exists?\n\n"
            "3. THE INFERENCE CHAIN IN SECTION 4 -- THIS IS THE PART DOING "
            "REAL WORK. Kenji argues: if backlog #23 finds audience-sensitive "
            "form selection, it can't have come from the Mackinlay lineage at "
            "the idiom level (since that lineage never encoded audience), so "
            "the sensitivity's source becomes independently worth tracing. "
            "Stress-test this. Is 'the formal literature is the dominant "
            "training signal for chart-design reasoning' a premise Kenji is "
            "entitled to, or is it asserted without support? Training data "
            "for a foundation model plainly includes far more than "
            "Mackinlay's lineage -- tutorials, journalism, marketing copy, "
            "Stack Overflow, design blogs discussing audience constantly. "
            "Does the chain overclaim how much a null result in the FORMAL "
            "literature tells you about the model's actual training "
            "distribution?\n\n"
            "4. SCOPE HONESTY. Kenji ran zero connector queries for this "
            "brief (read-and-analyze only) and says so plainly in the "
            "retrieval log. Is that the right call given the task, or should "
            "he have cross-checked the 'profile of a particular user' "
            "passage and the nested-model citation against anything else "
            "already in the corpus before writing the verdict?\n\n"
            "5. THE READING-PRIORITY LIST (section 5). Backlog #34 will be "
            "shaped by this. Does 'nested model chapter, then task "
            "abstraction chapter' actually follow from what the 5 slides "
            "show, or is Kenji guessing at book structure he hasn't seen?\n\n"
            "End with a clear recommendation: approved as-is, revise (name "
            "exactly what and why), or the verdict doesn't hold. This feeds "
            "directly into how the founder interprets Backlog #23 results "
            "later -- a comfortable pass is worth nothing here.\n\n"
            f"=== KENJI'S BRIEF ===\n{brief}\n\n"
            f"=== CURRENT HYPOTHESES, FOR CONTEXT ===\n{hypotheses}\n"
        )}],
    ) as stream:
        response = stream.get_final_message()

    review = response.content[0].text
    db.log_usage("ingrid", response.usage.input_tokens, response.usage.output_tokens)

    db.set_memory("ingrid", "gap_c_fulltext_review", review)
    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"review-task-{task_id}",
        text=review,
        metadata={"agent": "ingrid", "type": "gap_c_fulltext_review"},
    )
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/gap_c_fulltext_review"},
    )

    print(f"[{NAME}]\n\n{review}")
    print(f"\n\n--- {len(review)} chars, stored as ingrid/gap_c_fulltext_review ---")


if __name__ == "__main__":
    run()
