"""Sophie revises the Sprint 16 synthesis against Ingrid's close-gate
verdict (NEEDS_REVISION). Applies exactly the 5 required changes,
nothing else -- a correction pass, not a rewrite.
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
    if not synthesis or not gate:
        raise SystemExit("Missing synthesis or close gate.")

    if not db.get_memory("team_leader", "sprint16_synthesis_v1"):
        db.set_memory("team_leader", "sprint16_synthesis_v1", synthesis)
        print(f"[{NAME}] v1 preserved at team_leader/sprint16_synthesis_v1")

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="team_leader",
        title="Sprint 16 synthesis revision: apply Ingrid's 5 required changes",
        description="Correction pass only -- scope cut, count fix, new field, 2 dependency notes, entry-gate reclassification.",
    )

    client = OpenAI(api_key=os.environ["TEAM_LEADER_OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model=MODEL, max_completion_tokens=8000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                "Ingrid's Sprint 16 close-gate verdict was NEEDS_REVISION. "
                "Apply exactly her 5 required changes to the deliverable "
                "package. This is a correction pass -- reproduce the "
                "complete revised synthesis with these changes applied "
                "and nothing else altered (do not re-argue, restructure, "
                "or add new analysis beyond what's needed to apply these "
                "5 fixes):\n\n"
                "1. CUT the founder submission + infer-then-confirm UI "
                "workflow (image upload, LLM inference call, "
                "confirm/edit widget) from Sprint 17's in-scope list. "
                "REPLACE it with: a static fixture mechanism -- a small "
                "set of hard-coded or file-supplied (audience_code, "
                "goal_type) pairs the founder specifies directly, no LLM "
                "call, no widget, no vocabulary-finalization dependency. "
                "State plainly that this keeps Sprint 17 as a pure test "
                "of checkability, and that the full submission/inference "
                "workflow moves to Sprint 18 (where the web crawl and "
                "vocabulary finalization will also land).\n\n"
                "2. FIX the '6 vs 8 seed contracts' inconsistency -- the "
                "correct count is 8 (5 statistical-chart forms: violin, "
                "raincloud, beeswarm, dumbbell, KDE density; 3 non-chart "
                "forms: Slider, Carousel, Annotated Pyramid). Remove any "
                "remaining '6' references.\n\n"
                "3. ADD to the CheckResult design for the 3 non-chart "
                "contracts specifically: a mandatory human-readable "
                "annotation field stating which slots have NO equivalent "
                "in any chart-capable rendering environment -- populated "
                "at contract-authoring time by whoever defines the "
                "contract. State this is how Sprint 17 turns the "
                "behavioral-gravity risk into a concrete engineering "
                "finding instead of an unaddressed architectural risk.\n\n"
                "4. ADD two explicit Sprint 17 implementation "
                "dependencies to the open-questions section (not just "
                "list them as abstract questions): (a) the Minto/Zelazny "
                "tagging decision must be resolved BEFORE Sprint 17 "
                "writes Zelazny-derived content into any contract's "
                "what_it_asserts field; (b) the Annotated Pyramid "
                "contract is known-incomplete (missing MECE) -- either "
                "resolve the MECE decision before Sprint 17 implements "
                "the pyramid contract, or Sprint 17 must explicitly flag "
                "the pyramid's CheckResult output as 'contract definition "
                "incomplete -- pending MECE decision.'\n\n"
                "5. RECLASSIFY the checkability-bifurcation pre-build "
                "review (Priya/Kenji reviewing Mateo's finding before "
                "Sprint 17 builds anything) from an 'open question' to a "
                "SPRINT 17 ENTRY GATE -- a mandatory precondition before "
                "Sprint 17 starts, not an optional backlog item.\n\n"
                "Also note Ingrid's Process Review procedural finding "
                "(a Process Review covering sprints 13-16 will be "
                "genuinely due once Sprint 16 formally closes -- Sprint "
                "15 has now been retroactively closed for real, "
                "resolving the process gap Ingrid's math caught) -- state "
                "that this must be scheduled before or alongside Sprint "
                "17's opening.\n\n"
                "Output the complete revised deliverable package (all "
                "four parts: Concept Spec, Prior-art memo, Prototype "
                "Transition Plan, Open Questions/Risks) with these fixes "
                "applied. No preamble, no summary of what changed -- just "
                "the document.\n\n"
                f"=== INGRID'S FULL CLOSE-GATE REVIEW ===\n{gate}\n\n"
                f"=== YOUR SYNTHESIS TO REVISE ===\n{synthesis}\n"
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
        doc_id=f"sprint16-synthesis-v2-task-{task_id}",
        text=revised,
        metadata={"agent": "team_leader", "type": "sprint16_synthesis", "version": 2},
    )
    db.update_task(
        task_id, status="completed", result=revised,
        artifact_type="sprint_synthesis",
        artifact_payload={"memory_key": "team_leader/sprint16_synthesis", "version": 2},
    )

    print(f"[{NAME}]\n\n{revised}")
    print(f"\n\n--- v2 stored at team_leader/sprint16_synthesis, {len(revised)} chars ---")


if __name__ == "__main__":
    run()
