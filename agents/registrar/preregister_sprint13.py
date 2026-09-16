"""The Registrar writes Sprint 13's pre-registration -- predictions and
scoring rubric, locked before any Phase 1 pilot data exists.

Temporary role, mandate ends here. Kenji's Phase 0 protocol (as amended for
BASELINE/ORDER-only scope, R1/R2 clarifications, and the R3 knowledge-
elicitation probe) is the sole input. Ingrid's exact statistical plan
(McNemar's per model, no Bonferroni, ICC>=0.75 stopping rule) and JSC
reasoning-quality scheme are incorporated as given, not re-derived.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.registrar.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"


def run() -> None:
    require_tool("registrar", "write_preregistration")
    db.set_memory("registrar", "status", "online")

    protocol = db.get_memory("kenji", "sprint13_phase0_protocol") or ""
    gate = db.get_memory("ingrid", "sprint13_phase0_gate") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="registrar",
        title="Sprint 13 pre-registration",
        description="Locked before Phase 1 piloting. Registrar's mandate ends on delivery.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model=MODEL, max_tokens=6000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Write Sprint 13's pre-registration. This is the final Phase 0 "
            "deliverable -- once you submit this, your mandate ends, and it "
            "is not revised after Phase 1 piloting begins.\n\n"
            "PRODUCE:\n\n"
            "1. DIRECTIONAL PREDICTIONS, one each for BASELINE, ORDER, and "
            "the knowledge-elicitation probe. Each prediction must be "
            "falsifiable: state the specific direction, a numeric threshold "
            "where the protocol already gives you one (the probe prediction "
            "is already fully specified in the protocol's R3.6 -- use it "
            "verbatim, don't rederive it), and what observation would count "
            "as falsification. For BASELINE and ORDER, derive your own "
            "threshold-level prediction from what the protocol and prior "
            "sprint findings actually support -- ground each in something "
            "specific (a cited prior finding, a structural argument), not a "
            "round number picked for convenience.\n\n"
            "2. THE SCORING RUBRIC. Restate the primary form-match failure "
            "criterion (F1/F2/F3, from Kenji's protocol Section 1) as a "
            "rubric the Blind Scorer can apply cold, with zero knowledge of "
            "which condition or model produced an output. Critical "
            "constraint per your own persona: the rubric wording must not "
            "leak which condition is 'supposed' to look better -- no "
            "language implying a correct or expected outcome. Also restate "
            "the JSC reasoning-quality classification (Ingrid's gate "
            "review, Check 5) and the probe scoring criterion (R3.3) in the "
            "same cold, condition-blind form.\n\n"
            "3. THE CEILING-CONDITION PREDICTION. Kenji's protocol Section 3 "
            "specifies what 'maximal support' means operationally. State "
            "what result would count as H0 (no competence, unfixable) "
            "surviving even this condition -- be concrete about the "
            "threshold.\n\n"
            "4. WHAT YOU ARE NOT PREDICTING. State explicitly that AUDIENCE "
            "and GOAL conditions are out of scope for this pre-registration "
            "(deferred per the founder's scope narrowing) and that CORRUPTION "
            "and SUPPLY interventions are likewise out of scope for this "
            "sprint -- so nobody later treats this document as having made "
            "a prediction it didn't make.\n\n"
            "5. SIGN-OFF. A one-paragraph statement confirming: predictions "
            "were written without access to any pilot or real data, the "
            "rubric was checked against your own persona's constraint "
            "(rubric text must not predict which condition should score "
            "higher), and your mandate ends on delivery of this document -- "
            "you will not comment on results if asked.\n\n"
            f"=== KENJI'S FULL PHASE 0 PROTOCOL (including R1/R2/R3 amendments) ===\n{protocol}\n\n"
            f"=== INGRID'S GATE REVIEW (statistical plan, JSC scheme, contamination rules) ===\n{gate}\n"
        )}],
    ) as stream:
        resp = stream.get_final_message()

    prereg = resp.content[0].text
    db.log_usage("registrar", resp.usage.input_tokens, resp.usage.output_tokens)
    if resp.stop_reason == "max_tokens":
        prereg += "\n\n[TRUNCATED -- hit max_tokens, incomplete. Do not treat as locked until continued.]"

    db.set_memory("registrar", "sprint13_preregistration", prereg)
    vectorstore.remember(
        collection_name="team_leader_memory",
        doc_id=f"preregistration-task-{task_id}",
        text=prereg,
        metadata={"agent": "registrar", "type": "sprint13_preregistration"},
    )
    db.update_task(
        task_id, status="completed", result=prereg,
        artifact_type="preregistration",
        artifact_payload={"memory_key": "registrar/sprint13_preregistration"},
    )

    print(f"[{NAME}]\n\n{prereg}")
    print(f"\n\n--- {len(prereg)} chars, stored as registrar/sprint13_preregistration ---")


if __name__ == "__main__":
    run()
