"""Sprint 13, Phase 1 prerequisite: the controlled vocabulary Section 5 D4
requires but never actually enumerated.

Real gap found while building Phase 1 pilot scenarios (2026-09-16): the
protocol's D4 says audience/goal context is "drawn from a controlled
vocabulary of 6 audience descriptors... and 6 goal descriptors... "
established... from the Heer & Bostock and Zacks & Tversky findings" but
only ever gives 3 examples of each. R1's amendment confirmed the vocabulary
governs BASELINE/ORDER scenarios without the vocabulary itself ever being
completed. Closing it now, grounded in the same two citations already in
the record, before any scenario gets written.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    protocol = db.get_memory("kenji", "sprint13_phase0_protocol") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Complete the controlled vocabulary D4 references but never lists",
        description="Real gap found building Phase 1 pilot scenarios -- only 3 of 6 examples given for each list.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=2500, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Your Section 5 D4 references a controlled vocabulary of 6 "
            "audience descriptors and 6 goal descriptors, grounded in Heer "
            "& Bostock and Zacks & Tversky, but only ever gives 3 examples "
            "of each ('domain expert,' 'general public,' 'executive "
            "decision-maker' for audience; 'identify trend,' 'compare "
            "categories,' 'support a decision' for goal). The vocabulary "
            "was never actually completed. This blocks scenario "
            "construction -- close it now.\n\n"
            "Produce exactly 6 audience descriptors and exactly 6 goal "
            "descriptors. Requirements:\n\n"
            "- Each descriptor must be specific enough to satisfy your own "
            "Section 4 REJECTION CRITERION S3 (no bare job titles/"
            "professional stereotypes with predictable form preferences -- "
            "describe what the audience knows, needs to decide, or can "
            "receive, not a role label).\n"
            "- The 6 audience descriptors must be varied enough that "
            "different pairs of them would plausibly favor different visual "
            "forms for the same data (this is what makes ACCEPTANCE "
            "CRITERION A1 -- audience information load-bearing -- possible "
            "to satisfy).\n"
            "- The 6 goal descriptors must likewise be varied enough to be "
            "load-bearing, not synonyms of each other.\n"
            "- Ground the set in Heer & Bostock (perceptual "
            "effectiveness/task-based chart evaluation) and Zacks & Tversky "
            "(chart-reading as a cognitive task, action-affordances) -- "
            "state briefly, per descriptor or per pair, why it's grounded "
            "in those findings rather than invented ad hoc.\n\n"
            "Also: state explicitly whether audience and goal descriptors "
            "may be freely combined (any of 6 audience x any of 6 goal = 36 "
            "combinations), or whether only certain pairings are valid -- "
            "this determines how the 20 scenarios (once written) can be "
            "assigned.\n\n"
            f"=== YOUR FULL PHASE 0 PROTOCOL (for consistency) ===\n{protocol[-15000:]}\n"
        )}],
    )

    vocab = result.text
    db.log_usage("kenji", result.input_tokens, result.output_tokens)

    full = protocol + "\n\n---\n\n## AMENDMENT: Controlled Vocabulary, Completed (2026-09-16)\n\n" + vocab
    db.set_memory("kenji", "sprint13_phase0_protocol", full)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"brief-task-{task_id}",
        text=vocab,
        metadata={"agent": "kenji", "type": "controlled_vocabulary"},
    )
    db.update_task(
        task_id, status="completed", result=vocab,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/sprint13_phase0_protocol"},
    )

    print(f"[{NAME}] (continuations used: {result.continuations})\n\n{vocab}")
    print(f"\n\n--- {len(vocab)} chars, appended to kenji/sprint13_phase0_protocol ---")


if __name__ == "__main__":
    run()
