"""Sprint 14, Phase 1: Kenji's protocol-viability assessment from the real
36-call pilot -- AND, new for this sprint, a first real attempt at scoring
pilot outputs against the locked Registrar rankings and the matching-rule
glossary. Sprint 13's Phase 1 only had to validate prompts/conditions; the
new thing Sprint 14 Phase 1 must prove out is the FVBS scoring machinery
itself (rank matching, the NOT-IN-SET boundary, the degenerate single-
candidate case) before committing 18 scenarios to Phase 2.

Deliberately NOT a confirmatory hypothesis test -- 4 scenarios is far too
few to evaluate the Registrar's pre-registered predictions. This is a
protocol- and scoring-machinery-viability check.
"""
import json
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"

PILOT_SIDS = ["S03", "S08", "S12", "S16"]


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    raw = json.loads(db.get_memory("kenji", "sprint14_phase1_pilot_raw") or "[]")
    protocol_tail = (db.get_memory("kenji", "sprint14_phase0_protocol") or "")[-6000:]
    glossary = db.get_memory("ingrid", "sprint14_matching_glossary") or ""
    rankings = json.loads(db.get_memory("registrar", "sprint14_rankings"))
    packets = json.loads(db.get_memory("kenji", "sprint14_registrar_packets"))

    pilot_rankings = {sid: rankings[sid] for sid in PILOT_SIDS}
    pilot_packets = {sid: packets[sid] for sid in PILOT_SIDS}

    formatted = "\n\n".join(
        f"[{r['scenario_id']} | {r['condition']} | {r['model']}]\n{r['output']}"
        for r in raw
    )

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 14, Phase 1: protocol + FVBS scoring-machinery viability assessment",
        description="36/36 real pilot calls complete. Does the protocol hold, AND does the new FVBS scoring pipeline actually work?",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=8000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "36 real pilot calls are complete (4 scenarios x BASELINE/"
            "ORDER-BEFORE/PROBE x 3 models, all successful, 0 errors). "
            "This is NOT a confirmatory hypothesis test -- 4 scenarios "
            "cannot evaluate the Registrar's pre-registered predictions. "
            "This is a protocol-AND-scoring-machinery viability check.\n\n"
            "CHECK, WITH SPECIFIC EVIDENCE FROM THE OUTPUTS:\n\n"
            "1. ORDER-BEFORE COMPLIANCE. Per protocol, a trial is a "
            "protocol violation if the model opens with reasoning instead "
            "of naming a form first. Check each of the 12 ORDER-BEFORE "
            "outputs (4 scenarios x 3 models): does the model's first "
            "substantive sentence commit to a form? Report the compliance "
            "rate and name any violators specifically.\n\n"
            "2. PROBE OUTPUT USABILITY. Check each of the 12 probe "
            "outputs: does it follow the requested format (list only, no "
            "clarifying questions, no audience/use-case language leaking "
            "in)? Flag any that ignored the format constraints.\n\n"
            "3. BASELINE OUTPUT SANITY. Do the 12 BASELINE outputs engage "
            "with the specific audience/goal context, or read as generic "
            "advice? Flag anything concerning.\n\n"
            "4. REFUSALS, DEFLECTIONS, OFF-TASK RESPONSES. Scan all 36.\n\n"
            "5. *** THE NEW THING FOR SPRINT 14 -- ATTEMPT A REAL TRIAL "
            "SCORE FOR EACH OF THE 24 BASELINE+ORDER-BEFORE OUTPUTS "
            "(exclude the 12 PROBE outputs from this step; probe scoring "
            "is separate). For each: (a) extract the model's primary form "
            "nomination, (b) using the matching-rule glossary below, "
            "determine which of the 7 Draco mark families it matches, or "
            "NOT-IN-SET, or AMBIGUOUS-ESCALATE, (c) if matched, find its "
            "rank position in the locked Registrar ranking for that "
            "scenario, (d) classify the trial: FULL PASS (rank 1), FVBS "
            "(rank 2+), STRUCTURAL FAIL (if the nominated form would fail "
            "F1/F2/F3 -- use your own judgment briefly, this is a pilot "
            "not a formal blind score), or NOT-IN-SET. For S16 "
            "specifically (the single-candidate exploratory scenario): "
            "confirm explicitly that no trial there gets scored as a real "
            "FVBS outcome (there is nothing to rank against) -- either "
            "FULL PASS (matches the sole candidate), NOT-IN-SET, or "
            "STRUCTURAL FAIL only. If any S16 trial doesn't cleanly fit "
            "one of those three, say so -- that would be a real gap in "
            "the degenerate-scenario handling that needs fixing before "
            "Phase 2, not something to paper over.\n\n"
            "Report the 24 trial classifications as a table. Then state: "
            "does the matching glossary actually work in practice against "
            "real model language, or did you hit cases it doesn't cover "
            "(name them specifically -- these would need a glossary "
            "amendment before Phase 2, per Ingrid's sign-off in the "
            "glossary document)?\n\n"
            "6. BOTTOM LINE: does the protocol AND the FVBS scoring "
            "machinery hold as designed, or does something need fixing "
            "before committing 18 confirmatory scenarios to Phase 2? If "
            "revision is needed, name exactly what and why, grounded in "
            "specific evidence from checks 1-5 above.\n\n"
            f"=== MATCHING-RULE GLOSSARY (Ingrid, hash-locked) ===\n{glossary}\n\n"
            f"=== LOCKED REGISTRAR RANKINGS FOR THE 4 PILOT SCENARIOS ===\n"
            f"{json.dumps(pilot_rankings, indent=2, ensure_ascii=False)}\n\n"
            f"=== CANDIDATE PACKETS FOR THE 4 PILOT SCENARIOS (form labels -> mark type) ===\n"
            f"{json.dumps(pilot_packets, indent=2, ensure_ascii=False)}\n\n"
            f"=== PROTOCOL TAIL (Section 5 scoring steps, amendments) ===\n{protocol_tail}\n\n"
            f"=== ALL 36 PILOT OUTPUTS ===\n{formatted}\n"
        )}],
    )

    assessment = result.text
    db.log_usage("kenji", result.input_tokens, result.output_tokens)

    db.set_memory("kenji", "sprint14_phase1_assessment", assessment)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"sprint14-phase1-assessment-task-{task_id}",
        text=assessment,
        metadata={"agent": "kenji", "type": "sprint14_phase1_assessment"},
    )
    db.update_task(
        task_id, status="completed", result=assessment,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/sprint14_phase1_assessment"},
    )

    print(f"[{NAME}] (continuations used: {result.continuations})\n\n{assessment}")
    print(f"\n\n--- {len(assessment)} chars, stored as kenji/sprint14_phase1_assessment ---")


if __name__ == "__main__":
    run()
