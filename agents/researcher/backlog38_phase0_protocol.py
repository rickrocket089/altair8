"""Sprint 14, Phase 0: operationalize "audience-optimal" as a real,
falsifiable failure criterion -- the redesign Sprint 13's Section 5
specified in outline, now built to execution precision.

Framework, per Sophie's decisions this same session:
- Draco stays a data-structure-conformity check only (Option 3).
- The Registrar produces a per-scenario audience-optimal ranking of
  structurally valid forms, sealed before any model output exists --
  routed there instead of the Blind Scorer specifically to avoid the
  self-grading circularity Kenji's Option 3 check identified.
- Fresh data collection required (Ingrid's ruling): Kenji and the founder
  have already read the Sprint 13 outputs in detail, so a criterion built
  with that exposure isn't independent of what it's meant to test, even
  though the Registrar and Blind Scorer themselves stay genuinely blind.
- Same 20 scenarios as Sprint 13 (scenario construction itself isn't the
  contamination vector -- exposure to MODEL OUTPUTS is, and the scenarios
  were built before any model ran in Sprint 13 too).
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

    backlog_38 = next((i for i in db.list_backlog_items(status="open") if i["id"] == 38), None)
    section5 = db.get_memory("kenji", "sprint13_synthesis") or ""
    idx = section5.find("## 5. WHAT WOULD ACTUALLY TEST")
    section5_text = section5[idx:idx + 6000] if idx != -1 else ""
    option3_check = db.get_memory("kenji", "sprint14_option3_check") or ""
    scenarios = db.get_memory("kenji", "sprint13_scenarios") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 14, Phase 0: operationalize the audience-optimal criterion",
        description="Draco=structural layer only (Option 3, Version B); Registrar=ranking producer; fresh data collection required.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=8000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Build Sprint 14's Phase 0 protocol: the audience-optimal "
            "failure criterion, to execution precision -- your own Section "
            "5 outline (below) specified the direction, this makes it "
            "operational.\n\n"
            "IMPORTANT CONSTRAINT ON YOU SPECIFICALLY: you have read the "
            "Sprint 13 model outputs in detail during that synthesis. "
            "Ingrid's ruling (2026-09-16) is that this protocol must be "
            "designed on general principles from Section 5 and the "
            "scenario/vocabulary structure -- NOT shaped by memory of how "
            "any specific model answered any specific Sprint 13 scenario. "
            "Do not reference, even implicitly, which model got which "
            "scenario right or wrong in Sprint 13. If you catch yourself "
            "about to justify a design choice by appeal to a remembered "
            "Sprint 13 output, stop and re-ground the justification in the "
            "audience/goal vocabulary structure instead.\n\n"
            "PRODUCE:\n\n"
            "1. THE NEW FAILURE CATEGORY: 'form-valid-but-suboptimal.' "
            "Operational test: given the Registrar's locked ranking for "
            "this scenario, does the model's chosen form fall below a "
            "specified rank threshold (e.g. not the top-ranked form, or "
            "not within the top N)? Specify the exact threshold and your "
            "reasoning for it -- this is the core of the new instrument, "
            "be precise, not hand-wavy.\n\n"
            "2. RETAIN F1/F2/F3 as the structural-validity layer (Draco's "
            "domain, Option 3) -- a trial can fail on structural grounds "
            "OR on audience-optimality grounds OR both. Specify how these "
            "two failure types are recorded and reported separately (per "
            "Sprint 13's own lesson: don't let one failure type mask or "
            "merge with the other in the final tally).\n\n"
            "3. THE REGISTRAR'S RANKING TASK, fully specified: for each of "
            "the 20 scenarios, the Registrar produces an ordered list of "
            "structurally valid candidate forms (you should specify how "
            "many candidates -- e.g. 3-5 -- and where that candidate set "
            "comes from: Draco can supply structurally valid options via "
            "its existing constraint-satisfaction capability even without "
            "audience awareness, giving the Registrar a real candidate "
            "pool to RANK rather than inventing candidates from scratch) "
            "with a one-sentence audience-grounded rationale for each "
            "rank position. Specify exactly what information the Registrar "
            "receives (scenario data description + audience descriptor + "
            "goal descriptor -- same as what models see) and confirm they "
            "receive nothing about model outputs, past or present.\n\n"
            "4. SEQUENCING AND LOCKING, per the circularity fix: Registrar "
            "produces and submits all 20 rankings -> Ingrid reviews and "
            "locks them (Phase 0 gate) -> only then does Phase 1 piloting "
            "begin. Specify the lock mechanism (what makes a ranking "
            "genuinely unmodifiable after this point) -- same discipline "
            "as pre-registration.\n\n"
            "5. BLIND SCORER'S NEW TASK: given a locked ranking and a "
            "model output, determine the model's chosen form's rank "
            "position (or 'not in the candidate set' -- specify what that "
            "means and how it's scored) and apply the form-valid-but-"
            "suboptimal threshold from item 1. Keep this rubric as "
            "condition-blind as Sprint 13's was.\n\n"
            "6. WHAT STAYS THE SAME FROM SPRINT 13: the 20 scenarios "
            "(unchanged, already vetted), BASELINE + ORDER-BEFORE "
            "conditions, 3 models, the knowledge-elicitation probe design. "
            "Confirm explicitly what's being reused vs. rebuilt so nothing "
            "is silently different without a stated reason.\n\n"
            "7. REGISTRAR HANDOFF -- directional predictions for this "
            "sprint. Ground a real prediction about what fraction of "
            "trials will show form-valid-but-suboptimal failures, with "
            "reasoning that does NOT reference remembered Sprint 13 "
            "outputs -- ground it instead in the structural argument about "
            "convention-reproduction vs. genuine audience reasoning that "
            "motivated Backlog #23 in the first place.\n\n"
            f"=== YOUR SPRINT 13 SECTION 5 (the outline this operationalizes) ===\n{section5_text}\n\n"
            f"=== YOUR OPTION 3 CIRCULARITY CHECK ===\n{option3_check[:4000]}\n\n"
            f"=== BACKLOG #38 ===\n{backlog_38['description'] if backlog_38 else '(missing)'}\n\n"
            f"=== THE 20 SCENARIOS (reference only -- do not re-derive, just confirm reuse) ===\n{scenarios[:3000]}...[truncated, full set unchanged]\n"
        )}],
    )

    protocol = result.text
    db.log_usage("kenji", result.input_tokens, result.output_tokens)

    db.set_memory("kenji", "sprint14_phase0_protocol", protocol)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"brief-task-{task_id}",
        text=protocol,
        metadata={"agent": "kenji", "type": "sprint14_phase0_protocol"},
    )
    db.update_task(
        task_id, status="completed", result=protocol,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/sprint14_phase0_protocol"},
    )

    print(f"[{NAME}] (continuations: {result.continuations})\n\n{protocol}")
    print(f"\n\n--- {len(protocol)} chars, stored as kenji/sprint14_phase0_protocol ---")


if __name__ == "__main__":
    run()
