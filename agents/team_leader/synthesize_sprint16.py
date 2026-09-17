"""Sophie synthesizes Sprint 16's five-question deliverable package, per
her own Phase 0 brief: (1) Concept Spec (Q1/Q3/Q4/Q5), (2) Prior-art
memo (Q2), (3) Prototype Transition Plan for Sprint 17, (4) Open
Questions/Risks feeding the backlog. Interpretation and consolidation
only -- every finding below is already real, produced by Priya, Kenji,
the Knowledge Systems Architect, and Mateo across the sprint. Sophie
does not re-derive or re-litigate any of it.
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

    mechanism_sketches = db.get_memory("priya", "sprint16_mechanism_sketches") or ""
    priorart_check = db.get_memory("kenji", "sprint16_priorart_check") or ""
    minto_zelazny = db.get_memory("kenji", "minto_zelazny_distillation") or ""
    scaling_sketch = db.get_memory("knowledge_architect", "sprint16_scaling_sketch") or ""
    transition_consult = db.get_memory("mateo", "sprint16_transition_consult") or ""
    technical_prereqs = db.get_memory("mateo", "sprint16_technical_prerequisites") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="team_leader",
        title="Sprint 16 synthesis: Concept Spec, prior-art memo, Sprint 17 transition plan, open questions",
        description="Consolidate the 5 questions' real findings into the deliverable package.",
    )

    client = OpenAI(api_key=os.environ["TEAM_LEADER_OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model=MODEL, max_completion_tokens=8000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                "Synthesize Sprint 16's complete deliverable package. "
                "Every finding below is real work already done by Priya "
                "(Q1: mechanism sketches, chose Mechanism A -- "
                "Compositional Rendering Contracts), Kenji (Q2: prior-"
                "art check against Candidate #4/NL2INTERFACE as closest "
                "neighbor, plus a real gap-closing distillation of Minto/"
                "Zelazny), the Knowledge Systems Architect (Q3: scaling "
                "sketch, named the 'source-tier prior capture' failure "
                "mode), and Mateo (Q4: transition consult, found "
                "checkability bifurcates into slot-level vs. composition-"
                "rule-level; Q5: fully decided technical prerequisites). "
                "Your job is consolidation and interpretation, not "
                "re-derivation -- do not recompute or second-guess any "
                "of the concrete decisions already made (e.g. Mateo's "
                "SQLite/relational storage choice, the deferral of the "
                "web-crawl to Sprint 18).\n\n"
                "PRODUCE THE FOUR-PART DELIVERABLE PACKAGE:\n\n"
                "1. CONCEPT SPEC (answers Q1/Q3/Q4/Q5) -- a coherent "
                "narrative of what Mechanism A is, why it was chosen "
                "over Mechanisms B and C, how it scales (the three "
                "levels and the named failure mode + mitigations), what "
                "Sprint 17's transition plan is (Plan A: minimal "
                "environment declaration + contract checker, all 6 seed "
                "contracts, no ranking/crawl machinery), and the decided "
                "technical prerequisites. This is the primary reference "
                "document -- write it so someone who missed the sprint "
                "could pick it up and understand the architecture.\n\n"
                "2. PRIOR-ART MEMO (answers Q2) -- summarize Kenji's "
                "finding (Candidate #4/NL2INTERFACE closest neighbor, "
                "genuine combination-novelty in partial-satisfaction + "
                "variable-environment + communicative-completeness "
                "ranking together) AND the Minto/Zelazny distillation's "
                "implications (Zelazny's 5 relationship-to-form mappings "
                "as ready-to-use seeding for the statistical contracts' "
                "what_it_asserts field; MECE as a real gap in the "
                "Annotated Pyramid's composition rule).\n\n"
                "3. PROTOTYPE TRANSITION PLAN FOR SPRINT 17 -- concrete "
                "scope: Plan A only, all 6 seed contracts (5 statistical-"
                "chart forms from Sprint 14's NOT-IN-SET list -- violin, "
                "raincloud, beeswarm, dumbbell, KDE density -- plus the "
                "3 non-chart contracts: Slider, Carousel, Annotated "
                "Pyramid), the checkability bifurcation "
                "(slot-level vs. composition-rule-level) must be "
                "reflected in the CheckResult design, the founder's "
                "feeding mechanism (image + context + judgment, with the "
                "infer-then-confirm audience/goal widget) is IN scope, "
                "the web crawl is OUT of scope (Sprint 18). State this "
                "as Sprint 17's actual, bounded goal.\n\n"
                "4. OPEN QUESTIONS / RISKS FOR THE BACKLOG -- list each "
                "decision that was explicitly flagged as belonging to "
                "Sophie/founder rather than resolved by the team, with "
                "enough context to act on later: (a) should Minto/"
                "Zelazny be tagged as Candidate #2-style 'structured "
                "design knowledge with rationale' rather than source-"
                "tier convention attestation -- and does this retroactively "
                "apply to other McKinsey-origin material; (b) should "
                "MECE be added as a content-layer composition rule to "
                "the Annotated Pyramid contract, and should Minto's "
                "vertical-logic principle also become a contract "
                "constraint; (c) the vocabulary-finalization dependency "
                "Mateo flagged blocking the confirmation widget; (d) "
                "the checkability bifurcation finding needs review by "
                "Priya/Kenji before Sprint 17 builds anything, per "
                "Mateo's own instruction.\n\n"
                "End with a one-paragraph honest assessment: does this "
                "sprint's work actually satisfy the founder's original "
                "critique (that Draco-inherited vocabulary contradicted "
                "Design Principle #4 and the North Star), or does risk "
                "remain that the seed vocabulary stays chart-dominated "
                "in practice? Say plainly, don't hedge.\n\n"
                f"=== Q1: PRIYA'S MECHANISM SKETCHES (full) ===\n{mechanism_sketches}\n\n"
                f"=== Q2: KENJI'S PRIOR-ART CHECK (full) ===\n{priorart_check}\n\n"
                f"=== MINTO/ZELAZNY DISTILLATION (full) ===\n{minto_zelazny}\n\n"
                f"=== Q3: KNOWLEDGE ARCHITECT'S SCALING SKETCH (full) ===\n{scaling_sketch}\n\n"
                f"=== Q4: MATEO'S TRANSITION CONSULT (full) ===\n{transition_consult}\n\n"
                f"=== Q5: MATEO'S TECHNICAL PREREQUISITES (full) ===\n{technical_prereqs}\n"
            )},
        ],
    )

    synthesis = response.choices[0].message.content
    if response.choices[0].finish_reason == "length":
        synthesis += "\n\n[TRUNCATED -- hit max_completion_tokens, incomplete.]"
    db.log_usage("team_leader", response.usage.prompt_tokens, response.usage.completion_tokens)

    db.set_memory("team_leader", "sprint16_synthesis", synthesis)
    vectorstore.remember(
        collection_name="team_leader_memory",
        doc_id=f"sprint16-synthesis-task-{task_id}",
        text=synthesis,
        metadata={"agent": "team_leader", "type": "sprint16_synthesis"},
    )
    db.update_task(
        task_id, status="completed", result=synthesis,
        artifact_type="sprint_synthesis",
        artifact_payload={"memory_key": "team_leader/sprint16_synthesis"},
    )

    print(f"[{NAME}]\n\n{synthesis}")
    print(f"\n\n--- {len(synthesis)} chars, stored as team_leader/sprint16_synthesis ---")


if __name__ == "__main__":
    run()
