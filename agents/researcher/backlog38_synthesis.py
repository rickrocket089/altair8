"""Sprint 14, Phase 3: Kenji's synthesis of the real, computed FVBS
statistics. Interpretation only -- every number below is already real
and scipy-computed (backlog38_statistics.py); Kenji does not recompute,
round differently, or restate a number with more confidence than the
computation carries, same discipline as Sprint 13.
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

    statistics = db.get_memory("kenji", "sprint14_statistics_summary") or ""
    hypotheses = db.get_memory("team_leader", "hypotheses") or ""
    protocol_tail = (db.get_memory("kenji", "sprint14_phase0_protocol") or "")[-4000:]
    prereg_tail = (db.get_memory("registrar", "sprint14_preregistration") or "")[:6000]
    s03_ruling = db.get_memory("team_leader", "sprint14_s03_notinset_ruling") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 14, Phase 3: synthesis of real computed FVBS statistics",
        description="Interpret, don't calculate -- all numbers are already real and code-computed.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=8000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Synthesize Sprint 14's confirmatory results. The statistics "
            "below are real and already computed -- your job is "
            "interpretation, not arithmetic.\n\n"
            "PRODUCE:\n\n"
            "1. WHAT THE EVIDENCE SHOWS (strict observation, no "
            "interpretation yet): state the confirmatory FVBS rate, the "
            "stratified breakdown, the ORDER-BEFORE McNemar results per "
            "model, the NOT-IN-SET rate, and the probe results plainly, "
            "in that order.\n\n"
            "2. WHAT THIS MIGHT IMPLY -- the confirmatory FVBS rate "
            "(53.9%, within the pre-registered 40-65% range) is the "
            "central finding, and it is the opposite shape from Sprint "
            "13's ceiling result: this time the criterion DID "
            "discriminate. On more than half of structurally-valid "
            "trials, models chose a defensible-but-not-audience-optimal "
            "form rather than the actual best one. Address directly: "
            "does this support Sprint 13's 'Reading B' (F1/F2/F3 was "
            "measuring a categorically easier question than audience-"
            "optimality) now that a properly calibrated criterion shows "
            "a real gap? Say plainly whether this sprint's result reads "
            "as evidence for or against genuine audience reasoning in "
            "these models, and how confident that reading is given the "
            "95% CI (42.1-65.5%) spans a wide range of the pre-"
            "registered band.\n\n"
            "3. THE STRATIFICATION ANOMALY. The N=3-candidate stratum "
            "shows 88% FVBS (22/25) -- far above its own 33.3% random "
            "baseline and far above the N=2 (42.9%) and N=4 (35.1%) "
            "strata. This is only 25 trials across a handful of "
            "scenarios. Is this a real, informative pattern (something "
            "structurally different about 3-candidate scenarios) or is "
            "it more likely a small-sample artifact concentrated in 1-2 "
            "scenarios that happen to be hard? Say which, and what "
            "follow-up (if any) this warrants -- do not treat 88% as a "
            "headline number without this caveat.\n\n"
            "4. THE ORDER-BEFORE RESULT -- A DIFFERENT KIND OF NULL THAN "
            "SPRINT 13's. Sprint 13's McNemar was degenerate (zero "
            "variance to test). This sprint's is different: real "
            "variance exists, but 5-9 of 18 paired trials per model had "
            "to be EXCLUDED from each model's test because at least one "
            "condition produced a NOT_IN_SET or structural-fail outcome "
            "-- severely underpowering the test (n=9-13 pairs, all "
            "p=1.0 or degenerate). Distinguish this explicitly from "
            "Sprint 13's null: that one was 'no variance to test,' this "
            "one is 'a real test that couldn't reach significance at "
            "this sample size, further weakened by contamination from "
            "the NOT-IN-SET phenomenon eating into the paired sample.' "
            "Different cause, different fix (more scenarios/trials per "
            "model, not a different manipulation).\n\n"
            "5. THE NOT-IN-SET FINDING -- DO NOT COLLAPSE IT. Per "
            "Ingrid's explicit gate-review warning, the 26.7% NOT-IN-SET "
            "rate (vs. the pre-registered 5-20%) reflects three verified, "
            "distinct causes: (a) a genuine Draco-vocabulary ceiling "
            "(S03/S06/S09/S11/S19 -- dumbbell/violin/raincloud/beeswarm/"
            "KDE forms with no matching Draco mark type), (b) Draco's "
            "own cost-ranking excluding a real, F1/F2/F3-passing "
            "candidate from the top-4 cut (S20's line mark), and (c) a "
            "now-fixed scorer matching error (S14). State what each "
            "cause means for interpreting the result -- (a) is a real "
            "finding about tool/vocabulary limits and worth reporting as "
            "a substantive result; (b) is a methodology artifact of the "
            "top-4 cap, not a finding about models; (c) is already "
            "corrected and contributes nothing further. Give the "
            "corrected, disaggregated picture, not one number.\n\n"
            "6. WHAT WOULD FOLLOW FROM THIS SPRINT. Given a real, "
            "non-degenerate confirmatory result (unlike Sprint 13), what "
            "should happen next -- close the sprint on this finding, run "
            "a larger sample to power the ORDER-BEFORE test properly, "
            "investigate the vocabulary-ceiling finding as its own "
            "follow-up (Draco's mark vocabulary vs. what models actually "
            "reach for), or something else? Be concrete -- this is going "
            "into the sprint's closing outcome.\n\n"
            "7. RECOMMENDATION TO SOPHIE.\n\n"
            f"{statistics}\n\n"
            f"=== S03 NOT-IN-SET RULING, FOR CONTEXT (do not re-litigate) ===\n{s03_ruling}\n\n"
            f"=== CURRENT HYPOTHESES, FOR CONTEXT ===\n{hypotheses}\n\n"
            f"=== PROTOCOL TAIL ===\n{protocol_tail}\n\n"
            f"=== PRE-REGISTRATION HEAD ===\n{prereg_tail}\n"
        )}],
    )

    synthesis = result.text
    db.log_usage("kenji", result.input_tokens, result.output_tokens)

    db.set_memory("kenji", "sprint14_synthesis", synthesis)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"sprint14-synthesis-task-{task_id}",
        text=synthesis,
        metadata={"agent": "kenji", "type": "sprint14_synthesis"},
    )
    db.update_task(
        task_id, status="completed", result=synthesis,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/sprint14_synthesis"},
    )

    print(f"[{NAME}] (continuations: {result.continuations})\n\n{synthesis}")
    print(f"\n\n--- {len(synthesis)} chars, stored as kenji/sprint14_synthesis ---")


if __name__ == "__main__":
    run()
