"""Ingrid's independent check on the 4 redesigned scenarios
(backlog38_redesign_narrow_scenarios.py), before they're treated as
settled and folded into the Registrar packets.

Real reason this needs an independent pass, not just Kenji's own filter
check: the redesign (writing the new scenario, arguing why more mark
types should pass) and the F1/F2/F3 filter (checking whether they
actually do) both ran as the same persona in one script. That is exactly
the self-grading shape the Draco/Blind-Scorer split was built to avoid
earlier in this sprint -- the same author judging their own claim.
Checking all 4 here, not a sample, since the set is small and every one
of them is a scenario that previously failed to clear the bar.
"""
import json
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"

AUDIENCE = {
    "A1": "familiar with the measurement domain, unfamiliar with this specific dataset",
    "A4": "acts on a single viewing, under time pressure, no follow-up questions possible",
    "A5": "holds a strong prior belief, will scrutinize for confirming/disconfirming evidence",
}
GOAL = {
    "G1": "establish whether a directional change over time is monotonic, interrupted, or cyclical",
    "G4": "support a binary/multi-option choice, make the decision-relevant difference immediate",
    "G5": "identify whether variables move together, independently, or in opposition",
}

TARGET_SIDS = ["S03", "S07", "S14", "S16"]


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")

    redesigns = json.loads(db.get_memory("kenji", "sprint14_scenario_redesigns"))
    merged = json.loads(db.get_memory("kenji", "sprint14_final_candidatesets_v2"))
    kenji_filter = json.loads(db.get_memory("kenji", "sprint14_redesign_f123_filter"))

    items_block = ""
    for sid in TARGET_SIDS:
        r = redesigns[sid]
        kenji_pass = [c["mark_type"] for c in kenji_filter[sid] if c["overall"] == "PASS"]
        items_block += (
            f"\n\n=== {sid} ({r['cell']}) ===\n"
            f"Data: {r['data_description']}\n"
            f"Audience: {AUDIENCE[r['audience']]}\n"
            f"Goal: {GOAL[r['goal']]}\n"
            f"Kenji's own filter says PASS for: {kenji_pass}\n"
        )

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Independent check: 4 redesigned single-candidate scenarios (Sprint 14 middle path)",
        description=f"Kenji redesigned and filtered these himself in one pass -- verify independently. {TARGET_SIDS}",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=3000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Kenji redesigned these 4 scenarios (previously stuck at 1 "
            "valid Draco candidate each) to open up more structurally "
            "valid mark types, then ran his own F1/F2/F3 filter check on "
            "the redesigns in the same script run -- same author judging "
            "his own claim, the exact circularity risk this project has "
            "caught before. For each scenario, independently check every "
            "mark type he marked PASS: does it genuinely pass F1 "
            "(structurally valid), F2 (no explicit audience-constraint "
            "violation), and F3 (real commitment) for this specific "
            "redesigned data/audience/goal combination? State agreement "
            "or disagreement per mark type, with reasoning. If you "
            "disagree with any PASS, say so plainly -- do not defer to "
            "his verdict.\n\n"
            f"{items_block}\n\n"
            "Close with: for each of the 4 scenarios, your own count of "
            "genuinely valid mark types, and whether the redesign should "
            "be accepted as-is, needs another iteration, or (for S07 "
            "specifically, which Kenji's own check left at only 1) "
            "whether it's fundamentally a structurally hard case."
        )}],
    )
    check = result.text
    db.log_usage("ingrid", result.input_tokens, result.output_tokens)

    db.set_memory("ingrid", "sprint14_redesign_spotcheck", check)
    db.update_task(
        task_id, status="completed", result=check,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/sprint14_redesign_spotcheck"},
    )

    print(f"[{NAME}]\n\n{check}")
    print("\n\n--- stored as ingrid/sprint14_redesign_spotcheck ---")


if __name__ == "__main__":
    run()
