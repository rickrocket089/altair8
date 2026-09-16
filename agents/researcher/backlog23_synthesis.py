"""Sprint 13, Phase 3: Kenji's synthesis of the real, computed statistics.

All numbers below were computed via scipy (binomtest, exact McNemar on
discordant pairs), not estimated by an LLM -- Kenji is interpreting
results, not calculating them. This is deliberate: arithmetic from a
language model is exactly the kind of thing the Reported-Success Trap
warns about for a confirmatory hypothesis test.
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

REAL_STATISTICS = """
=== REAL, CODE-COMPUTED STATISTICS (scipy binomtest / exact McNemar on
discordant pairs -- not LLM-estimated) ===

H1 -- BASELINE FAILURE RATE (pre-registered: 15-65%):
Observed: 0/60 = 0.0% (0/20 per model, all three models, zero exceptions)
VERDICT: FALSIFIED. 0% is below the pre-registered 15% floor.

H2 -- ORDER-BEFORE vs BASELINE, exact McNemar per model:
claude-sonnet-4-6:   [[PP=20,PF=0],[FP=0,FF=0]] -- DEGENERATE, zero discordant pairs
gpt-5.2:              [[PP=20,PF=0],[FP=0,FF=0]] -- DEGENERATE, zero discordant pairs
gemini-flash-latest:  [[PP=20,PF=0],[FP=0,FF=0]] -- DEGENERATE, zero discordant pairs
No model produced a single ORDER-BEFORE-induced form-match failure. McNemar's
test is undefined for a fully concordant table -- there is no discordant
information for the test to evaluate. This is not "no effect found," it is
"the outcome variable had zero variance to test against."

JSC-B (form-first) PROPORTION, BASELINE vs ORDER-BEFORE, descriptive with 95% CI:
claude-sonnet-4-6:   BASELINE 0/20 (0.0%, CI [0.0%,16.8%]) -> ORDER-BEFORE 5/20 (25.0%, CI [8.7%,49.1%])
gpt-5.2:              BASELINE 8/20 (40.0%, CI [19.1%,63.9%]) -> ORDER-BEFORE 7/20 (35.0%, CI [15.4%,59.2%])
gemini-flash-latest:  BASELINE 7/20 (35.0%, CI [15.4%,59.2%]) -> ORDER-BEFORE 13/20 (65.0%, CI [40.8%,84.6%])
Direction predicted (ORDER-BEFORE > BASELINE): confirmed in 2/3 models (claude,
gemini), not confirmed in gpt-5.2 (moved slightly the other way). Registered as
non-confirmatory/descriptive only, per the pre-registration.

PROBE PASS RATE per model, with 95% CI (ground truth = Draco alone, weak signal
per Sophie/Ingrid's ruling on the single-tool-not-consensus deviation):
claude-sonnet-4-6:   13/20 = 65.0%, CI [40.8%,84.6%]
gpt-5.2:              13/20 = 65.0%, CI [40.8%,84.6%]
gemini-flash-latest:  12/20 = 60.0%, CI [36.1%,80.9%]
Registered prediction was about K1a/K1b split among BASELINE FAILURES, not
about raw probe pass rate -- see below for why that specific prediction
cannot be evaluated.

K1a/K1b DIAGNOSTIC (registered prediction: >=60% of BASELINE failures are K1a):
BASELINE FAIL cases available: 0
VERDICT: UNTESTABLE. The registered prediction has an empty denominator --
zero BASELINE failures means there is no "among BASELINE failures" population
to classify as K1a or K1b. This is a precondition failure, not a null result.
Backlog #37 (K1a vs K1b) remains genuinely unresolved by this sprint, despite
the probe running cleanly and producing real, varied data on its own terms
(the 60-65% PROBE PASS rates above are real and usable for other purposes,
just not for the specific registered K1a/K1b split).
"""


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    hypotheses = db.get_memory("team_leader", "hypotheses") or ""
    protocol_tail = (db.get_memory("kenji", "sprint13_phase0_protocol") or "")[-4000:]
    prereg_tail = (db.get_memory("registrar", "sprint13_preregistration") or "")[:6000]

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 13, Phase 3: synthesis of real computed statistics",
        description="Interpret, don't calculate -- all numbers are already real and code-computed.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=8000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Synthesize Sprint 13's confirmatory results. The statistics "
            "below are real and already computed -- your job is "
            "interpretation, not arithmetic. Do not recompute, round "
            "differently, or restate a number with more confidence than "
            "the computation itself carries.\n\n"
            "PRODUCE:\n\n"
            "1. WHAT THE EVIDENCE SHOWS (strict observation, no "
            "interpretation yet): state H1, H2, the JSC pattern, the probe "
            "results, and the K1a/K1b untestability plainly, in that "
            "order.\n\n"
            "2. WHAT THIS MIGHT IMPLY -- H1's total falsification is the "
            "central finding. The pre-registered 15% floor was itself "
            "derived from a specific argument (Section 1.1 of the "
            "pre-registration: models have 'some' relevant knowledge per "
            "Section 7's prior, but non-scripted scenarios should still "
            "produce non-trivial failure). Zero failures across 60 trials, "
            "3 models, is not just 'better than expected' -- it may mean "
            "the F1/F2/F3 criterion (structural incapacity / explicit "
            "constraint violation / no commitment) is measuring a "
            "categorically easier question than what Backlog #23 actually "
            "wanted tested (does the model choose the AUDIENCE-OPTIMAL "
            "form, not just a STRUCTURALLY VALID one). Address this "
            "directly: is the null result evidence that frontier models "
            "have essentially solved structural form selection, or is it "
            "evidence that the operational failure criterion doesn't "
            "capture the phenomenon Backlog #23 was built to study? Both "
            "readings are available from this data -- say which the "
            "evidence favors and why, without overclaiming either.\n\n"
            "3. WHAT THE McNEMAR DEGENERACY MEANS FOR H2/H5 (the ORDER "
            "intervention). The intervention couldn't move an outcome "
            "variable that never varied. This does not confirm H5 "
            "(reasoning is decorative) -- it means this specific design "
            "couldn't test H5 at all, for a different reason than the K1a/"
            "K1b untestability. Distinguish these two 'untestable' results "
            "from each other clearly -- they have different causes and "
            "different fixes.\n\n"
            "4. THE JSC SECONDARY PATTERN -- 2/3 models moved in the "
            "predicted direction (more form-first justification under "
            "ORDER-BEFORE), gpt-5.2 did not. This was registered as "
            "descriptive/non-confirmatory. Say what it's still worth, "
            "given that. Is gpt-5.2's divergence worth a note for future "
            "sprints, or noise at this sample size?\n\n"
            "5. WHAT WOULD ACTUALLY TEST WHAT BACKLOG #23 WANTED. Given "
            "that F1/F2/F3 turned out to be too permissive to produce any "
            "failures at all, what would a finer-grained criterion need to "
            "capture -- specifically, how would you operationalize "
            "'audience-optimal' rather than 'structurally valid,' and what "
            "would that require from the ground-truth layer (recall: "
            "Layer 1 is Draco alone now, not 3-tool consensus)?\n\n"
            "6. RECOMMENDATION TO SOPHIE. Given a completely null result on "
            "the primary and secondary confirmatory tests (not from a "
            "design flaw exactly, but from a criterion calibrated more "
            "leniently than the phenomenon warranted), what should happen "
            "next -- rerun with a stricter criterion, treat this sprint's "
            "finding itself as the result (frontier models pass a basic "
            "structural-validity bar reliably), or something else? Be "
            "concrete, this is going into the sprint's closing outcome.\n\n"
            f"{REAL_STATISTICS}\n\n"
            f"=== CURRENT HYPOTHESES, FOR CONTEXT ===\n{hypotheses}\n\n"
            f"=== PROTOCOL TAIL (F1/F2/F3 origin, Section 1) ===\n{protocol_tail}\n\n"
            f"=== PRE-REGISTRATION HEAD (predictions as registered) ===\n{prereg_tail}\n"
        )}],
    )

    synthesis = result.text
    db.log_usage("kenji", result.input_tokens, result.output_tokens)

    db.set_memory("kenji", "sprint13_synthesis", synthesis)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"brief-task-{task_id}",
        text=synthesis,
        metadata={"agent": "kenji", "type": "sprint13_synthesis"},
    )
    db.update_task(
        task_id, status="completed", result=synthesis,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/sprint13_synthesis"},
    )

    print(f"[{NAME}] (continuations: {result.continuations})\n\n{synthesis}")
    print(f"\n\n--- {len(synthesis)} chars, stored as kenji/sprint13_synthesis ---")


if __name__ == "__main__":
    run()
