"""Sophie's third and (expected) final revision pass on the Sprint 16
synthesis, against Ingrid's third close-gate verdict -- much narrower
than rounds 1-2, explicitly confirming "the plan may proceed with these
additions, none requires scope expansion."
"""
import os

from dotenv import load_dotenv
from openai import OpenAI

from agents.permissions import require_tool
from agents.team_leader.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "gpt-5.2"


def run() -> None:
    require_tool("team_leader", "read_all")
    db.set_memory("team_leader", "status", "online")

    synthesis = db.get_memory("team_leader", "sprint16_synthesis") or ""
    gate = db.get_memory("ingrid", "sprint16_close_gate") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="team_leader",
        title="Sprint 16 synthesis revision v4: apply Ingrid's third gate findings",
        description="Fix stale Process Review language, set Minto/Zelazny decision deadline+fallback, add comparative CheckResult table, 2 minor clarifications.",
    )

    client = OpenAI(api_key=os.environ["TEAM_LEADER_OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model=MODEL, max_completion_tokens=8000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                "Ingrid's third Sprint 16 close-gate verdict is "
                "NEEDS_REVISION but explicitly narrow -- she states "
                "'the plan may proceed with these additions, none "
                "requires scope expansion.' Apply exactly her 3 required "
                "items plus 2 minor clarifications, nothing else:\n\n"
                "1. FIX THE STALE PROCESS REVIEW LANGUAGE. Process Review "
                "#4 (covering Sprints 13-15) has ALREADY BEEN CONDUCTED "
                "by Ingrid -- it is complete, not pending. Remove any "
                "language describing it as still due or as a blocking "
                "gate still to be initiated. State plainly: 'Process "
                "Review #4 (Sprints 13-15) was conducted by Ingrid and is "
                "complete. Its 9 structural actions (S-19 through S-27) "
                "should be actioned before Sprint 17 opens per Ingrid's "
                "own recommendation, but no Process Review is currently "
                "due (0 sprints since the last review).'\n\n"
                "2. SET A DEADLINE + FALLBACK for the Minto/Zelazny "
                "tagging decision: if not resolved by Sprint 17's third "
                "day, the default is provisional tagging as 'structured "
                "design knowledge with rationale' (the reading Ingrid "
                "herself endorsed), flagged as provisional, with "
                "retroactive reclassification applied post-sprint if the "
                "founder later decides otherwise. State this explicitly "
                "-- this decision blocks authoring for 5 of 8 contracts "
                "(the statistical-chart forms) if left undeadlined.\n\n"
                "3. ADD a named Sprint 17 output artifact: a one-page "
                "comparative table, produced after all 8 contracts run "
                "through the checker, listing per contract: slot count, "
                "slots satisfied/partial/unsatisfied/uncertain against "
                "the declared environment, and composition-rule findings "
                "by their three-state status. Purpose: not to rank "
                "contracts in Sprint 17, but to make visible whether "
                "chart and non-chart contracts produce systematically "
                "different CheckResult shapes -- giving Sprint 18's "
                "ranking design a real empirical starting point instead "
                "of inheriting behavioral-gravity risk blindly.\n\n"
                "4. MINOR: state explicitly that contract definition (8 "
                "knowledge-engineering tasks: slots, composition rules, "
                "what_it_asserts content) is Sprint 17's PRIMARY "
                "deliverable, not assumed prerequisite setup work.\n\n"
                "5. MINOR: state explicitly that the 'flag CheckResult as "
                "contract-definition-incomplete' path for Annotated "
                "Pyramid is the DEFAULT if the MECE decision isn't made "
                "in time -- not a fallback held as equally likely to "
                "resolving MECE first. Also fix the open-question (c) "
                "block: vocabulary finalization is now correctly a "
                "Sprint 18 dependency only (the Sprint 17 risk was "
                "already resolved by deferring the confirmation widget) "
                "-- update the block so it doesn't read as an unresolved "
                "Sprint 17 risk.\n\n"
                "Output the complete revised deliverable package (all "
                "four parts) with these 5 fixes applied. No preamble, no "
                "changelog -- just the document.\n\n"
                f"=== INGRID'S THIRD CLOSE-GATE REVIEW (full) ===\n{gate}\n\n"
                f"=== CURRENT SYNTHESIS TO REVISE ===\n{synthesis}\n"
            )},
        ],
    )

    revised = response.choices[0].message.content
    if response.choices[0].finish_reason == "length":
        revised += "\n\n[TRUNCATED -- hit max_completion_tokens, incomplete.]"
    db.log_usage("team_leader", response.usage.prompt_tokens, response.usage.completion_tokens)

    db.set_memory("team_leader", "sprint16_synthesis", revised)
    vectorstore.remember(
        collection_name="team_leader_memory",
        doc_id=f"sprint16-synthesis-v4-task-{task_id}",
        text=revised,
        metadata={"agent": "team_leader", "type": "sprint16_synthesis", "version": 4},
    )
    db.update_task(
        task_id, status="completed", result=revised,
        artifact_type="sprint_synthesis",
        artifact_payload={"memory_key": "team_leader/sprint16_synthesis", "version": 4},
    )

    print(f"[{NAME}]\n\n{revised}")
    print(f"\n\n--- v4 stored at team_leader/sprint16_synthesis, {len(revised)} chars ---")


if __name__ == "__main__":
    run()
