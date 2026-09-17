"""Sprint 16, Question 5 (final): Mateo lists the technical prerequisites
for Mechanism A, as decidable items -- not a wishlist. Builds directly on
his own Q4 transition consult (which already specified the Contract and
RenderingEnvironment data structures and the checker interface) rather
than re-deriving them.

Covers: data/corpus requirements (informed by the founder's own two
feeding mechanisms -- personal expert-curated examples from his daily
work, and a web crawl that feeds both vocabulary discovery and ranking),
knowledge storage architecture (graph vs. embeddings vs. hybrid -- the
founder asked this directly; the team's answer must be concrete, not a
restatement), runtime components, and observability without human
studies.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.developer.persona import NAME, SYSTEM_PROMPT
from agents.permissions import require_tool
from tools import db, vectorstore
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"

FOUNDER_FEEDING_CONTEXT = """FOUNDER-SPECIFIED FEEDING MECHANISMS (2026-09-17), both already
decided, both must be accounted for in the technical prerequisites -- not re-litigated:

1. PERSONAL EXPERT-CURATED FEEDING: the founder will use the system in his own daily work to
   submit real examples -- a form he encountered, its real context (e.g. "used for a Steering
   Committee"), and his own judgment of why it worked. This is high-trust, low-volume, human-
   sourced evidence -- a 4th evidence tier distinct from source-tier-prior, human-in-the-loop-
   queue-scored, and (hypothetical future) validated outcome data.
2. WEB-CRAWL FEEDING: crawls business-communication artifacts (annual reports, consulting
   decks) for BOTH vocabulary discovery (what forms exist) AND ranking evidence (source-tier
   quality prior, per the founder's explicit decision that the crawl feeds ranking too, not
   just vocabulary).

A REAL DESIGN REQUIREMENT FROM THE FOUNDER'S FEEDING MECHANISM: when the founder submits an
example with only informal context ("this was for a SteerCo"), the system should PROPOSE an
inferred audience/goal classification (using the LLM's background knowledge about what a
SteerCo audience typically implies) and have the founder CONFIRM OR CORRECT it with minimal
friction -- not silently trust the inference (this would re-introduce the same audience-
resolution unreliability Sprint 14 already measured at ~54% failure), and not force the founder
to manually fill out the full controlled vocabulary every time (defeats the point of quick daily
capture). The inferred vs. confirmed status must be tagged and kept distinguishable, same
provenance discipline as the Architect's source-tier tagging."""


def run() -> None:
    require_tool("mateo", "write_task_artifact")
    db.set_memory("mateo", "status", "online")

    mechanism_sketches = db.get_memory("priya", "sprint16_mechanism_sketches") or ""
    mech_a_start = mechanism_sketches.find("## Mechanism Sketch A")
    mech_a_end = mechanism_sketches.find("## Mechanism Sketch B")
    mechanism_a = mechanism_sketches[mech_a_start:mech_a_end] if mech_a_start != -1 else mechanism_sketches[:4000]

    own_q4_consult = db.get_memory("mateo", "sprint16_transition_consult") or ""
    scaling_sketch = db.get_memory("knowledge_architect", "sprint16_scaling_sketch") or ""
    operating_model = scaling_sketch[scaling_sketch.find("## Level 3"):scaling_sketch.find("## Handoff Summary")]

    minto_zelazny = db.get_memory("kenji", "minto_zelazny_distillation") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="mateo",
        title="Sprint 16, Q5: technical prerequisites for Mechanism A",
        description="Decidable items, not a wishlist. Builds on Mateo's own Q4 consult.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=6000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Sprint 16, Question 5 of 5 (final question): list the "
            "technical prerequisites for Mechanism A as DECIDABLE "
            "ITEMS -- each one should be answerable with a concrete "
            "choice and a reason, not left as an open wishlist. Build "
            "on your own Q4 consult (the Contract, RenderingEnvironment, "
            "and CheckResult data structures are already specified -- "
            "do not redo that work, reference it).\n\n"
            "1. DATA / CORPUS REQUIREMENTS. Given the founder's two "
            "feeding mechanisms (personal expert-curated examples + web "
            "crawl, both specified below), what does the system "
            "concretely need to accept as input? Specify: what format "
            "does a founder-submitted example take (be concrete -- "
            "image upload? text description? both?), what does the "
            "'propose inferred audience/goal, human confirms' interface "
            "actually require technically (this is a real, buildable "
            "requirement, not a hand-wave), and what does the web-crawl "
            "ingestion pipeline need at minimum for Sprint 17's scope "
            "(if it's even in scope -- say plainly if you think it "
            "should be deferred past Sprint 17 given the founder-feeding "
            "mechanism alone might be sufficient for a first prototype).\n\n"
            "2. KNOWLEDGE STORAGE ARCHITECTURE. The founder asked "
            "directly: is this a knowledge graph, embeddings, or "
            "something else? Give a concrete, decided answer -- not a "
            "restatement of tradeoffs. State what the actual storage "
            "choice is for Sprint 17's minimal scope (contract registry "
            "+ whatever evidence structure is needed for the founder's "
            "feeding mechanism), and name the concrete technology choice "
            "if you have one in mind (e.g. a specific graph DB, a "
            "relational schema, a vector store + metadata) given this "
            "is a small-scale prototype, not the scaled system the "
            "Knowledge Architect sketched.\n\n"
            "3. RUNTIME COMPONENTS. What real runtime pieces are needed "
            "beyond the contract checker you already specified: is a "
            "constraint solver needed, or is contract-matching simple "
            "enough not to need one? Is a planner needed, or is direct "
            "retrieval sufficient for Sprint 17's scope? Be concrete "
            "about what's needed NOW vs. what's needed only once ranking "
            "and multiple candidate contracts are in play (later "
            "sprints).\n\n"
            "4. OBSERVABILITY WITHOUT HUMAN STUDIES. How do we check "
            "whether the system is working, for Sprint 17's scope, "
            "without running a human study? What can be verified "
            "mechanically (e.g. does the checker's output match a "
            "manually worked example) vs. what genuinely requires "
            "judgment (and whose judgment -- Ingrid's? the founder's own "
            "feeding-and-checking loop?).\n\n"
            "5. LINK TO TVIR / CANDIDATE #2 IF RELEVANT. Does either "
            "offer a concrete technical building block (not just "
            "conceptual precedent) worth reusing -- e.g. TVIR's actual "
            "confirmed implementation (agent/, benchmark/, E2B sandbox) "
            "-- or is this a case where the conceptual similarity "
            "doesn't extend to reusable code/infrastructure? Give a "
            "direct answer.\n\n"
            f"{FOUNDER_FEEDING_CONTEXT}\n\n"
            f"=== MECHANISM A ===\n{mechanism_a}\n\n"
            f"=== YOUR OWN Q4 CONSULT (data structures already specified) ===\n{own_q4_consult[:6000]}\n\n"
            f"=== KNOWLEDGE ARCHITECT'S OPERATING MODEL (Q3) ===\n{operating_model[:4000]}\n\n"
            f"=== MINTO/ZELAZNY DISTILLATION, FOR CONTEXT ===\n{minto_zelazny[:2000]}\n"
        )}],
    )

    prerequisites = result.text
    db.log_usage("mateo", result.input_tokens, result.output_tokens)

    db.set_memory("mateo", "sprint16_technical_prerequisites", prerequisites)
    vectorstore.remember(
        collection_name="developer_memory",
        doc_id=f"sprint16-prerequisites-task-{task_id}",
        text=prerequisites,
        metadata={"agent": "mateo", "type": "sprint16_technical_prerequisites"},
    )
    db.update_task(
        task_id, status="completed", result=prerequisites,
        artifact_type="brief",
        artifact_payload={"memory_key": "mateo/sprint16_technical_prerequisites"},
    )

    print(f"[{NAME}] (continuations: {result.continuations})\n\n{prerequisites}")
    print(f"\n\n--- {len(prerequisites)} chars, stored as mateo/sprint16_technical_prerequisites ---")


if __name__ == "__main__":
    run()
