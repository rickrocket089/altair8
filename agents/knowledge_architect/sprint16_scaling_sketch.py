"""Sprint 16, Question 3: the Knowledge Systems Architect (temp role)
sketches how the Mechanism A contract vocabulary/ranking could scale
across three levels -- knowledge coverage, expressive vocabulary,
operating model (QA/versioning/drift/weak supervision).

Incorporates two founder-specified weak-supervision mechanisms for the
communicative-completeness ranking (2026-09-17), which the founder
explicitly decided should be fed by the web-crawl corpus, not just
vocabulary discovery:
1. Human-in-the-loop scoring for cases with no clear signal ("show me
   everything we have, I give the score").
2. Source-tier quality prior: content from certain source types (annual
   reports, McKinsey/BCG-class decks) is assumed generally good as a
   CONVENTION PRIOR, not proof of audience-optimality -- flagged
   explicitly as source-trust, distinct from validated outcome data, per
   Candidate #11's own "convention prior, not target" framing and
   Unstated Bet B (prestige/production quality != reader comprehension).

The Architect does not design the knowledge layer's content or mechanism
(Priya's job) and does not select or rank Priya's concepts -- design/
architecture only, no code, no real data.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.knowledge_architect.persona import NAME, SYSTEM_PROMPT
from agents.permissions import require_tool
from tools import db, vectorstore
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"

FOUNDER_WEAK_SUPERVISION_INPUT = """FOUNDER DECISION (2026-09-17): the web-crawl corpus
(business-communication artifacts + their visualizations/context) feeds BOTH
vocabulary discovery AND the communicative-completeness ranking -- not vocabulary
discovery alone. Two concrete weak-supervision mechanisms specified:

1. HUMAN-IN-THE-LOOP SCORING: where no clear signal exists to derive a rank
   automatically, leave the rank empty rather than guessing, and surface it for
   manual scoring later ("show me everything we have, I give the score").

2. SOURCE-TIER QUALITY PRIOR: content sourced from certain source types (e.g.
   annual/financial reports, McKinsey/BCG-class consulting decks) is assumed
   generally good BY DEFAULT -- a convention-prior heuristic, explicitly not
   validated outcome data. Must be tagged as source-trust in the data model, kept
   distinguishable from any future real outcome signal (per Candidate #11's own
   "convention prior, not target" framing, and per Unstated Bet B -- prestige/
   production quality is not the same claim as reader comprehension)."""


def run() -> None:
    require_tool("knowledge_architect", "write_brief")
    db.set_memory("knowledge_architect", "status", "online")

    mechanism_sketches = db.get_memory("priya", "sprint16_mechanism_sketches") or ""
    mech_a_start = mechanism_sketches.find("## Mechanism Sketch A")
    mech_a_end = mechanism_sketches.find("## Mechanism Sketch B")
    mechanism_a = mechanism_sketches[mech_a_start:mech_a_end] if mech_a_start != -1 else mechanism_sketches[:5000]

    priorart_check = db.get_memory("kenji", "sprint16_priorart_check") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="knowledge_architect",
        title="Sprint 16, Q3: scaling sketch for Mechanism A's knowledge base",
        description="3 levels: coverage, expressive vocabulary, operating model. Includes 2 founder weak-supervision mechanisms.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=6000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Sprint 16, Question 3 of 5: sketch how Mechanism A's "
            "knowledge base (contract vocabulary + communicative-"
            "completeness ranking) could scale, across your three "
            "assigned levels. This includes two founder-specified "
            "weak-supervision mechanisms you must incorporate concretely "
            "into the operating-model level, not just acknowledge.\n\n"
            f"{FOUNDER_WEAK_SUPERVISION_INPUT}\n\n"
            "For LEVEL 1 (knowledge coverage): how does the contract "
            "vocabulary and its ranking data grow across more domains, "
            "audiences (the 6-code vocabulary), and goals -- given the "
            "web-crawl is now a real intended source, not hypothetical? "
            "Name concrete volume/velocity assumptions where you can "
            "(order-of-magnitude is fine), and name what breaks first as "
            "coverage grows.\n\n"
            "For LEVEL 2 (expressive vocabulary): how does the PRIMITIVE "
            "SET itself grow beyond the seed (chart forms + the 3 "
            "non-chart seed contracts already specified: Slider, "
            "Carousel, Annotated Pyramid) without losing the "
            "compositional discipline that makes the architecture "
            "valuable? What stops this from becoming an unstructured "
            "grab-bag of one-off contracts?\n\n"
            "For LEVEL 3 (operating model): this is where the founder's "
            "two weak-supervision mechanisms must be designed concretely, "
            "not just restated. Specifically:\n"
            "- How does the human-in-the-loop scoring queue actually "
            "work operationally -- what triggers an item entering the "
            "queue, what does the reviewer see, how does a manual score "
            "get versioned and re-derived if criteria change later?\n"
            "- How does the source-tier prior get implemented as data -- "
            "what does a 'source-trust' tag look like, how many tiers, "
            "how is it kept structurally distinguishable from real "
            "outcome data so it can never be silently promoted to "
            "'validated' status?\n"
            "- What is the actual failure mode this two-mechanism design "
            "is most exposed to at scale? Name it plainly -- don't "
            "present this as solved. Consider specifically: does the "
            "source-tier prior risk becoming the DE FACTO ranking "
            "(because it's cheap and automatic) while human-in-the-loop "
            "scoring (expensive, manual) never catches up in volume -- "
            "meaning the system converges on 'ranked by prestige of "
            "source' rather than anything resembling audience-"
            "optimality? If you see this risk, name a concrete "
            "mitigation, not just the risk.\n\n"
            "Standard scaling concerns to address within these three "
            "levels: versioning, QA, drift detection, and the "
            "structured-vs-retrieval-heavy tradeoff for the knowledge "
            "representation. Name what breaks first at scale for each "
            "level -- a scaling sketch with no named breaking point is "
            "not useful.\n\n"
            f"=== MECHANISM A (Priya's sketch) ===\n{mechanism_a}\n\n"
            f"=== KENJI'S PRIOR-ART CHECK (incl. the 3 non-chart seed "
            f"contracts already specified) ===\n{priorart_check[priorart_check.find('CHECK 4'):]}\n"
        )}],
    )

    scaling_sketch = result.text
    db.log_usage("knowledge_architect", result.input_tokens, result.output_tokens)

    db.set_memory("knowledge_architect", "sprint16_scaling_sketch", scaling_sketch)
    vectorstore.remember(
        collection_name="knowledge_architect_memory",
        doc_id=f"sprint16-scaling-task-{task_id}",
        text=scaling_sketch,
        metadata={"agent": "knowledge_architect", "type": "sprint16_scaling_sketch"},
    )
    db.update_task(
        task_id, status="completed", result=scaling_sketch,
        artifact_type="brief",
        artifact_payload={"memory_key": "knowledge_architect/sprint16_scaling_sketch"},
    )

    print(f"[{NAME}] (continuations: {result.continuations})\n\n{scaling_sketch}")
    print(f"\n\n--- {len(scaling_sketch)} chars, stored as knowledge_architect/sprint16_scaling_sketch ---")


if __name__ == "__main__":
    run()
