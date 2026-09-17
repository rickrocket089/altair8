"""Sprint 15: Kenji's reality-check pass on Priya's 4 knowledge-layer
concepts, per Sophie's process design -- runs strictly AFTER Priya's
blind concept generation, not before (so her concepts aren't steered).

Per Sophie's spec: for each concept, annotate only (a) "supported by
what we already ingested/found" (yes/no + source), (b) "conflicts with
Sprint 14 failure evidence?" (yes/no), (c) "missing critical paper/tool
from candidate list #1/#2/#11?" (yes/no). Max one page per concept --
this is a grounding check, not a second design pass. Kenji does not
rank or select; that is Ingrid's diversity/honesty gate and then the
founder's call.
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

    concepts = db.get_memory("priya", "sprint15_concepts") or ""
    if not concepts:
        raise SystemExit("Missing priya/sprint15_concepts -- run generate_concepts_sprint15.py first.")

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 15: reality-check pass on Priya's 4 knowledge-layer concepts",
        description="Grounding check only -- not a second design pass, not a ranking.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=6000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Reality-check Priya's 4 Sprint 15 concepts (ACFR, FGE, AAEB, "
            "CCO) -- generated for a visualization-knowledge layer "
            "centered on Candidate #11, optionally combined with #1 "
            "(TVIR) and #2 (Structured Visualization Design Knowledge). "
            "This is a grounding check, not a second design pass and not "
            "a ranking -- you do not select a winner.\n\n"
            "For EACH of the 4 concepts, in max one page, answer exactly "
            "these three questions with a yes/no plus grounding:\n\n"
            "(a) SUPPORTED BY WHAT WE ALREADY INGESTED/FOUND? Does the "
            "concept's core mechanism already appear, in whole or "
            "substantial part, in literature or systems this team has "
            "actually retrieved and confirmed (not just heard of) -- "
            "name the specific source (paper, tool, candidate approach "
            "number) if yes. If you are not certain something exists but "
            "suspect it might, say that explicitly rather than a flat "
            "yes/no -- do not assert confirmation you don't have.\n\n"
            "(b) CONFLICTS WITH SPRINT 14 FAILURE EVIDENCE? Does the "
            "concept's proposed mechanism contradict, or rest on an "
            "assumption falsified by, anything Sprint 13/14 actually "
            "found (the 0/120 structural-failure result, the 53.9% FVBS "
            "rate, the 3-cause NOT-IN-SET breakdown, the underpowered "
            "ORDER-BEFORE result)? Be specific about which finding, if "
            "any.\n\n"
            "(c) MISSING CRITICAL PAPER/TOOL FROM #1/#2/#11? Given what "
            "you know of TVIR's actual implementation, the Structured "
            "Visualization Design Knowledge paper, and Candidate #11's "
            "own on-record history (including its binding objection), "
            "is there something specific and load-bearing that a "
            "concept's design depends on but doesn't account for? Name "
            "it precisely -- a vague 'more literature might help' is not "
            "useful here.\n\n"
            "You do not rank the concepts or recommend one. If you have "
            "an observation that applies across multiple concepts rather "
            "than to one specifically, state it separately at the end "
            "under 'CROSS-CUTTING OBSERVATIONS' rather than repeating it "
            "four times.\n\n"
            f"=== PRIYA'S 4 CONCEPTS (FULL) ===\n{concepts}\n"
        )}],
    )

    reality_check = result.text
    db.log_usage("kenji", result.input_tokens, result.output_tokens)

    db.set_memory("kenji", "sprint15_reality_check", reality_check)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"sprint15-reality-check-task-{task_id}",
        text=reality_check,
        metadata={"agent": "kenji", "type": "sprint15_reality_check"},
    )
    db.update_task(
        task_id, status="completed", result=reality_check,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/sprint15_reality_check"},
    )

    print(f"[{NAME}] (continuations: {result.continuations})\n\n{reality_check}")
    print(f"\n\n--- {len(reality_check)} chars, stored as kenji/sprint15_reality_check ---")


if __name__ == "__main__":
    run()
