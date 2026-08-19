"""Ingrid's gate on Sprint 10 Pass 1. Pass 2 cannot run until this passes.

Her own blocking item 2: blindness is a property of the input the model
actually received, not of the orchestrator's intent, so it must be evidenced
and inspected rather than asserted.

She checks two things, not one:
  (a) the INPUT -- did any excluded prior art reach the prompt? She is given
      the real candidate_approaches rows and the Sprint 9 primitive names to
      search against, so she is checking against actual exclusions rather than
      a description of them.
  (b) the OUTPUT -- did Priya honour blocking item 1, the Pass 1 field 3
      constraint (justify novelty against the constraint set and failure data,
      never against named prior approaches)? Nobody has checked this yet, and
      a violation there is evidence of leaked context even if the prompt looks
      clean.

A failed gate means Pass 1 is rerun, not patched.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

SPRINT9_PRIMITIVES = (
    "scrollytelling with a pinned visual; annotation-led reading path; "
    "force-directed relationship graph; diegetic information display; "
    "template reproduction. Plus the 11 surveyed patterns from data "
    "journalism, motion graphics, spatial/AR, game UI and scientific "
    "visualization."
)


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Gate: verify Sprint 10 Pass 1 was genuinely run blind",
        description="Blocking gate. Pass 2 cannot run without a pass verdict.",
    )

    input_log = db.get_memory("priya", "sprint10_pass1_input") or "(missing)"
    concepts = db.get_memory("priya", "sprint10_concepts_blind") or "(missing)"

    rows = db.list_candidate_approaches()
    exclusions = "\n".join(
        f"  - [{r.get('category')}] {r.get('title')}" for r in rows
    ) or "  (none found)"

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "This is the gate you required as blocking item 2 of your "
                    "Sprint 10 design review. Pass 2 does not run until you "
                    "return a verdict. A failed gate means Pass 1 is rerun, "
                    "not patched.\n\n"
                    "THE MATERIAL THAT WAS SUPPOSED TO BE EXCLUDED — these are "
                    "the actual candidate_approaches rows from Postgres, not a "
                    "description of them:\n"
                    f"{exclusions}\n\n"
                    f"Also excluded: {SPRINT9_PRIMITIVES}\n"
                    "Also excluded: Sprint 8's pipeline architecture and its "
                    "4-stage structure; any named third-party tool from "
                    "Kenji's landscape scans.\n\n"
                    "================ THE PASS 1 INPUT LOG ================\n"
                    f"{input_log}\n\n"
                    "================ PRIYA'S PASS 1 OUTPUT ================\n"
                    f"{concepts}\n\n"
                    "================ YOUR TASK ================\n\n"
                    "1. INPUT CHECK. Read the verbatim system prompt and user "
                    "message in the log. Did any excluded material reach "
                    "Priya, in name or in recognisable paraphrase? Be "
                    "specific: quote anything you flag. Also judge whether the "
                    "log is genuinely complete — if you cannot verify a claim "
                    "it makes (e.g. that no vectorstore query ran), say so "
                    "rather than accepting it.\n\n"
                    "2. OUTPUT CHECK — your blocking item 1. The Pass 1 field "
                    "3 constraint required Priya to justify novelty against "
                    "the constraint set and failure data only, never against "
                    "named prior approaches, and to avoid 'unlike [system]' "
                    "framing. Did she comply, in all five concepts? Quote any "
                    "violation.\n\n"
                    "3. LEAKAGE INFERENCE. Independent of the prompt: does "
                    "anything in the five concepts suggest Priya had access to "
                    "the excluded material anyway? Distinguish clearly between "
                    "(a) evidence of leaked context, and (b) convergence with "
                    "prior art through pretraining, which this design "
                    "explicitly expects and does not treat as a failure. "
                    "Getting this distinction wrong in either direction is the "
                    "main risk in your judgement here.\n\n"
                    "4. Does the output meet the sprint's success criterion "
                    "(a): at least 3 concepts complete across all eight "
                    "fields? Check field completeness properly, including "
                    "whether field 6 states an observation, a measure AND a "
                    "threshold as required. Name any concept that falls "
                    "short.\n\n"
                    "5. Anything else you would flag before Pass 2 runs — "
                    "including any problem with the concepts themselves that "
                    "is better caught now than after the sighted pass "
                    "contaminates the comparison.\n\n"
                    "End with: PASS 1 CONFIRMED BLIND — Pass 2 may proceed, or "
                    "PASS 1 NOT CONFIRMED — with exactly what must be rerun "
                    "and why."
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
        metadata={"agent": "ingrid", "type": "sprint10_pass1_blindness_gate"},
    )
    db.set_memory("ingrid", "sprint10_pass1_blindness_gate", review)
    db.update_task(
        task_id, status="completed", result=review,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/sprint10_pass1_blindness_gate"},
    )

    print(f"[{NAME}]\n\n{review}")
    print(f"\n\n--- {len(review)} chars ---")


if __name__ == "__main__":
    run()
