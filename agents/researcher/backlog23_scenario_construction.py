"""Sprint 13: construct the actual 20 scenarios from the 6x6 vocabulary
grid, per Sophie's sampling decision (2026-09-16): 8 extreme cells (max
constraint on both axes, both crossings), 8 mid-grid cells (2 per
quadrant, for generalizability), 4 cells Kenji picks and justifies himself.
A4xG4 is mandatory in the 8 extreme cells per Sophie's explicit instruction.

Each scenario must pass Section 4's three rejection criteria (S1 no
recognizable professional genre, S2 not answerable by domain convention
alone, S3 audience not a bare stereotype) and both acceptance criteria (A1
audience information load-bearing, A2 data description form-agnostic), use
the D3 fixed template (domain label, variable count, variable types,
one-sentence pattern description, no narrative embellishment), and at
least 6 of the 20 must meet the NOVEL-CONTEXT definition (Section 4.2).

Also checks, per Sophie's explicit instruction: does this cell selection
run against anything the Registrar already pre-registered? The Registrar's
predictions are aggregate (failure-rate ranges, directional effects across
all 20 scenarios), not scenario-specific, so there should be no conflict --
Kenji confirms this explicitly rather than assuming it.
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
    prereg = db.get_memory("registrar", "sprint13_preregistration") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Construct the 20 Sprint 13 scenarios",
        description="Per Sophie's cell-sampling decision: 8 extreme, 8 mid-grid, 4 Kenji's choice.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=8000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Construct the 20 scenarios per Sophie's sampling decision:\n"
            "- 8 EXTREME cells: maximal constraint on both axes (high-"
            "constraint audience x high-constraint goal, low x low, and "
            "both crossings). A4 x G4 is mandatory in this set -- do not "
            "re-justify it, just include it.\n"
            "- 8 MID-GRID cells: distributed evenly across the grid, two "
            "per quadrant, for generalizability.\n"
            "- 4 cells of YOUR OWN CHOICE: pick whichever 4 remaining cells "
            "you find most methodologically interesting given the "
            "vocabulary, and justify each choice in one sentence. This is "
            "an explicit slot for your judgment, not a formality.\n\n"
            "For EACH of the 20 scenarios, produce:\n"
            "1. Scenario ID (S01-S20) and the audience/goal cell it's drawn "
            "from (e.g., A4xG4).\n"
            "2. The data description, using the fixed D3 template: domain "
            "label, variable count, variable types (categorical/"
            "continuous), one-sentence pattern description. No narrative "
            "embellishment, no visual-form vocabulary, no emotionally "
            "valenced language.\n"
            "3. A one-line self-check against each of S1, S2, S3, A1, A2 -- "
            "state pass/fail for each, don't just assert the scenario is "
            "fine. If any check would fail, redesign the scenario before "
            "including it -- do not include a scenario that fails its own "
            "checks.\n"
            "4. NOVEL-CONTEXT flag: yes/no, per the Section 4.2 definition "
            "(unfamiliar visualization domain AND non-standard audience "
            "category). At least 6 of the 20 must be flagged yes -- track "
            "this as you go and adjust scenario choices if you're short.\n\n"
            "After all 20: \n"
            "A. Confirm the novel-context count (must be >=6).\n"
            "B. CHECK AGAINST THE PRE-REGISTRATION: the Registrar's "
            "predictions are aggregate (BASELINE failure rate 15-65% "
            "across all 20; ORDER-BEFORE degrading in >=2/3 models; probe "
            "K1a >=60% among BASELINE failures) -- confirm explicitly that "
            "nothing about which 20 cells were chosen could mechanically "
            "force or preclude these aggregate outcomes (e.g. if all 20 "
            "scenarios were trivially easy, the 15% floor would be at "
            "risk regardless of what the study finds). State your "
            "confidence in this confirmation.\n"
            "C. Which of the 20 will you use for Phase 1 PILOTING (2-3 "
            "scenarios, per the protocol's Phase 1 spec) before the full "
            "run -- name them and say why those specifically (e.g. one "
            "extreme, one mid, one novel-context, to stress-test the "
            "protocol across the range).\n\n"
            f"=== YOUR FULL PHASE 0 PROTOCOL (includes the completed vocabulary) ===\n{protocol[-25000:]}\n\n"
            f"=== REGISTRAR'S PRE-REGISTRATION (for the cross-check) ===\n{prereg[:10000]}\n"
        )}],
    )

    scenarios = result.text
    db.log_usage("kenji", result.input_tokens, result.output_tokens)

    db.set_memory("kenji", "sprint13_scenarios", scenarios)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"brief-task-{task_id}",
        text=scenarios,
        metadata={"agent": "kenji", "type": "sprint13_scenarios"},
    )
    db.update_task(
        task_id, status="completed", result=scenarios,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/sprint13_scenarios"},
    )

    print(f"[{NAME}] (continuations used: {result.continuations})\n\n{scenarios}")
    print(f"\n\n--- {len(scenarios)} chars, stored as kenji/sprint13_scenarios ---")


if __name__ == "__main__":
    run()
