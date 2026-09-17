"""Sprint 16, Question 2: Kenji checks whether Mechanism A (Compositional
Rendering Contracts, Priya's Sprint 16 Q1 "real bet") already exists,
against the team's own prior research -- not a new broad literature scan.

Includes two founder contributions (2026-09-17) that must be explicitly
addressed, not just filed:
1. A concrete seeding idea for the contract vocabulary: crawl the web for
   business-communication artifacts and store visualizations WITH their
   context. Kenji must check this against Candidate #11's own on-record
   binding objection (a corpus of existing artifacts records what people
   DID, not what WORKED -- no outcome variable) rather than treating it
   as a fresh idea free of that history.
2. A named INTERMEDIATE FORM CATEGORY, between full data visualization
   and plain text: correct placement/presentation of facts that aren't
   chart-shaped at all -- when to use a slider, a carousel, a photo, a
   pyramid with text elements, etc. This is closer to general information/
   interaction design patterns than to "visualization" narrowly, and
   needs its own prior-art check, separate from the chart-vocabulary
   question.
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

    mechanism_sketches = db.get_memory("priya", "sprint16_mechanism_sketches") or ""
    mech_a_start = mechanism_sketches.find("## Mechanism Sketch A")
    mech_a_end = mechanism_sketches.find("## Mechanism Sketch B")
    mechanism_a = mechanism_sketches[mech_a_start:mech_a_end] if mech_a_start != -1 else mechanism_sketches[:5000]
    real_bet = mechanism_sketches[mechanism_sketches.find("## The Real Bet"):]

    candidate_11_record = db.get_memory("team_leader", "sprint15_input_brief_for_priya") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 16, Q2: prior-art check for Mechanism A (Compositional Rendering Contracts)",
        description="Checked against our own prior research, not a new scan. Two founder inputs must be addressed explicitly.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=6000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Sprint 16, Question 2 of 5: are we reasonably confident "
            "Mechanism A (Compositional Rendering Contracts -- Priya's "
            "named 'real bet' from Sprint 16 Q1) doesn't already exist? "
            "Check against our own prior research and candidate "
            "approaches -- this is NOT a new broad literature scan.\n\n"
            "CHECK 1 -- CLOSEST NEIGHBORS. Compare Mechanism A's core "
            "idea (a form is stored as a capability-contract with "
            "partial-satisfaction scoring against what the rendering "
            "environment can actually execute, ranked by communicative "
            "completeness rather than Draco-style cost) against: "
            "Candidate #1 (TVIR), #2 (Structured Visualization Design "
            "Knowledge), #4 (NL2INTERFACE/SmartMLVs), #5 (PPTAgent/"
            "PPTEval), and any other candidate approach or ingested full "
            "text you have actual confirmed retrieval of. Name the "
            "closest neighbor precisely and state what is genuinely new "
            "about Mechanism A versus it -- and what is not new (be "
            "honest where overlap is real, don't manufacture novelty).\n\n"
            "CHECK 2 -- FOUNDER INPUT: WEB-CRAWL SEEDING IDEA. The "
            "founder proposed seeding the contract vocabulary by "
            "crawling the web for business-communication artifacts and "
            "storing visualizations WITH their context. Do not treat "
            "this as a fresh idea -- it is a concrete instance of "
            "Candidate #11 (corpus of existing artifacts as knowledge "
            "structure), which already has an on-record BINDING "
            "OBJECTION: a corpus of existing artifacts records what "
            "people DID, not what WORKED -- there is no outcome "
            "variable. Apply that objection directly to this seeding "
            "idea as applied to Mechanism A specifically: does storing "
            "'visualization + context' from a web crawl give the "
            "contract's communicative-completeness ranking anything it "
            "doesn't already have from Draco's cost function -- or does "
            "it just replace one unvalidated ranking source with "
            "another? State plainly what WOULD make web-crawled context "
            "usable (an outcome signal of some kind) versus what "
            "wouldn't (pure frequency/attestation).\n\n"
            "CHECK 3 -- FOUNDER INPUT: THE INTERMEDIATE FORM CATEGORY. "
            "The founder named a category between full data "
            "visualization and plain text: correct placement/"
            "presentation of facts that aren't chart-shaped at all -- "
            "when to use a slider, a carousel, a photo, a pyramid with "
            "text elements, etc. This is closer to general information/"
            "interaction design patterns than to 'visualization' "
            "narrowly. Check: does this category already have prior art "
            "in what we've retrieved (UI pattern libraries, "
            "presentation-design tools like PPTAgent, interaction design "
            "literature, NL2INTERFACE's multi-view assemblies)? Is this "
            "category something Mechanism A's contract architecture can "
            "represent without modification (Priya's sketch claims "
            "contracts don't care what the primitives are), or does it "
            "require an actual extension to the mechanism? Answer "
            "concretely, don't just restate that contracts are "
            "general-purpose.\n\n"
            "CHECK 4 -- SEED VOCABULARY RISK, VERIFIED. Priya flagged "
            "that Mechanism A's seed vocabulary risks being chart-only "
            "if populated only from Sprint 14's NOT-IN-SET list, and "
            "required at least 2 non-chart-shaped contracts in the seed "
            "as a structural requirement. Does the founder's "
            "intermediate-form category (Check 3) give us real, "
            "concrete candidates for those non-chart seed contracts "
            "(e.g. a slider-contract, a carousel-contract)? Name 2-3 "
            "specific ones if so.\n\n"
            "Do not rank or select -- Mechanism A is already chosen. "
            "Your job is grounding, not re-deciding.\n\n"
            f"=== MECHANISM A (Priya's sketch, in full) ===\n{mechanism_a}\n\n"
            f"=== PRIYA'S 'REAL BET' REASONING ===\n{real_bet}\n\n"
            f"=== CANDIDATE #11'S ON-RECORD BINDING OBJECTION (context for Check 2) ===\n"
            f"{candidate_11_record[:3000]}\n"
        )}],
    )

    priorart_check = result.text
    db.log_usage("kenji", result.input_tokens, result.output_tokens)

    db.set_memory("kenji", "sprint16_priorart_check", priorart_check)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"sprint16-priorart-task-{task_id}",
        text=priorart_check,
        metadata={"agent": "kenji", "type": "sprint16_priorart_check"},
    )
    db.update_task(
        task_id, status="completed", result=priorart_check,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/sprint16_priorart_check"},
    )

    print(f"[{NAME}] (continuations: {result.continuations})\n\n{priorart_check}")
    print(f"\n\n--- {len(priorart_check)} chars, stored as kenji/sprint16_priorart_check ---")


if __name__ == "__main__":
    run()
