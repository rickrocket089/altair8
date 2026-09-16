"""The Registrar's formal Sprint 14 pre-registration -- rewritten fresh
per Backlog #38 item C (Sophie's ruling: methodologically cleaner to
rewrite against the new FVBS criterion than reuse Sprint 13's predictions,
which were written against F1/F2/F3 alone). Same Registrar instance/run
as the rankings (rank_sprint14_candidates.py) -- both are pre-registration
deliverables and both lock together per Kenji's Phase 0 protocol
amendment (Section 4, item 2: rankings AND pre-registration both required
before Phase 1 begins).

Input is Kenji's Phase 0 protocol Section 7 (the directional grounding
argument and the 35-55% FVBS-rate prediction) plus the real, disclosed
deviation this Registrar run surfaced: candidate-set sizes are variable
per scenario (1-6, not a uniform 4), so the random baseline is 1/N per
scenario, not a uniform 25%. The Registrar must reason about what that
does to the aggregate prediction, not just restate Section 7's number
as if nothing changed.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.registrar.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"


def run() -> None:
    require_tool("registrar", "write_preregistration")
    db.set_memory("registrar", "status", "online")

    protocol = db.get_memory("kenji", "sprint14_phase0_protocol") or ""
    baselines = db.get_memory("registrar", "sprint14_ranking_baselines") or ""
    sprint13_prereg = db.get_memory("registrar", "sprint13_preregistration") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="registrar",
        title="Sprint 14 pre-registration (rewritten fresh, FVBS criterion)",
        description="Locked together with the 20 rankings before Phase 1 piloting.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=6000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Write Sprint 14's pre-registration -- a fresh document, not a "
            "revision of Sprint 13's (that document stands on record, "
            "written against F1/F2/F3 alone, and is not overwritten). This "
            "is a separate gate condition from the 20 rankings you already "
            "produced; both lock together before Phase 1 begins.\n\n"
            "PRODUCE:\n\n"
            "1. THE DIRECTIONAL PREDICTION for the FVBS rate (form-valid-"
            "but-suboptimal: structurally valid but not ranked 1st in your "
            "own locked rankings). Kenji's protocol Section 7 argues for "
            "35-55%, reasoned from a fixed assumption of 4 candidates per "
            "scenario and a uniform 25% random baseline. THAT ASSUMPTION "
            "NO LONGER HOLDS: the real candidate-set sizes you just ranked "
            "range from 1 to 6 per scenario (2 scenarios, S07 and S16, "
            "have only 1 candidate each and are exploratory-only, excluded "
            "from the confirmatory FVBS analysis; the 18 main-analysis "
            "scenarios range 2-6). State your own prediction accounting "
            "for this -- do not just restate Kenji's 35-55% number "
            "unexamined. Reason about what variable N does to the "
            "aggregate rate and to the interpretation of any given "
            "scenario's result (a FVBS on a 2-candidate scenario is a "
            "much weaker signal than a FVBS on a 6-candidate scenario). "
            "Give a concrete range and what would falsify it.\n\n"
            "2. THE ORDER-BEFORE EFFECT prediction Section 7 deferred to "
            "you -- state a specific magnitude and falsification "
            "condition for whether the ordering instruction reduces the "
            "FVBS rate relative to BASELINE.\n\n"
            "3. WHAT YOU ARE NOT PREDICTING. State explicitly that S07 and "
            "S16 (single-candidate, exploratory-only) are excluded from "
            "any confirmatory FVBS prediction -- you may note what you'd "
            "expect there only as non-binding exploratory commentary, "
            "clearly separated from the confirmatory predictions.\n\n"
            "4. THE NOT-IN-SET rate prediction -- per Sophie's ruling this "
            "is now its own pre-registered secondary outcome (tracked "
            "separately, not folded into FVBS). State a directional "
            "prediction and falsification condition for how often models "
            "nominate a form outside your candidate set entirely.\n\n"
            "5. SIGN-OFF. Confirm: these predictions were written with "
            "zero knowledge of any Phase 1 or Phase 2 data, after you "
            "completed the rankings but before any model has been run "
            "under Sprint 14's protocol; your mandate ends on delivery.\n\n"
            f"=== KENJI'S FULL PHASE 0 PROTOCOL ===\n{protocol}\n\n"
            f"=== REAL PER-SCENARIO BASELINES FROM YOUR OWN RANKING RUN ===\n{baselines}\n\n"
            f"=== SPRINT 13'S PRE-REGISTRATION, FOR CONTEXT ONLY (do not revise it, "
            f"cite only if genuinely relevant) ===\n{sprint13_prereg[:3000]}\n"
        )}],
    )

    prereg = result.text
    db.log_usage("registrar", result.input_tokens, result.output_tokens)

    db.set_memory("registrar", "sprint14_preregistration", prereg)
    vectorstore.remember(
        collection_name="team_leader_memory",
        doc_id=f"sprint14-preregistration-task-{task_id}",
        text=prereg,
        metadata={"agent": "registrar", "type": "sprint14_preregistration"},
    )
    db.update_task(
        task_id, status="completed", result=prereg,
        artifact_type="preregistration",
        artifact_payload={"memory_key": "registrar/sprint14_preregistration"},
    )

    print(f"[{NAME}]\n\n{prereg}")
    print(f"\n\n--- {len(prereg)} chars, stored as registrar/sprint14_preregistration ---")


if __name__ == "__main__":
    run()
