"""Sprint 13, Phase 0: operationalize the failure before explaining it.

Backlog #23's own text is explicit that this has never been done: "We have
never defined what counts as a failure instance; that is why Sprint 10's
criterion (b) failed and why Phase C keeps slipping." This produces the
actual protocol -- the four intervention operationalizations, the scenario
design constraints (non-scripted, per Naledi's Sprint 7 culturally-scripted-
scenario finding), the ceiling condition, and the ground-truth-convergence
check -- that everything downstream (Registrar's pre-registration, Phase 1
piloting, Phase 2's full run) depends on.

Design notes folded in from prior sprints, per Sophie's Sprint 13 plan:
- Novel-context conditions (Bangalore & Stent grounding, Sprint 12)
- Item-level positional/compositional measurement sensitivity (Danescu
  grounding, Sprint 12)
- K1a (browser expressive ceiling) vs K1b (agent reliable-generation
  ceiling) named explicitly as an observation dimension, not resolved
  (backlog #37 -- the gap Sophie's triage found)
- The two OVERLAPS Kenji's prior-art check flagged ("Scaffold, Not
  Vocabulary?"; ChartAgent) cited for context, differentiated, not treated
  as blocking
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    backlog_23 = next((i for i in db.list_backlog_items(status="open") if i["id"] == 23), None)
    backlog_37 = next((i for i in db.list_backlog_items(status="open") if i["id"] == 37), None)
    prior_art = db.get_memory("kenji", "backlog23_prior_art_check") or ""
    sprint12_synthesis = db.get_memory("kenji", "sprint12_gap_ab_reading") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 13, Phase 0: operationalize the failure",
        description="Backlog #23's own prerequisite before anything else runs.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model=MODEL, max_tokens=8000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Produce Sprint 13's Phase 0 protocol. This is the operational "
            "definition Backlog #23 itself says has never existed -- "
            "everything downstream (a Registrar's pre-registered "
            "predictions, Phase 1 piloting, Phase 2's full run) depends on "
            "what you specify here being precise enough to execute without "
            "ambiguity.\n\n"
            "PRODUCE, IN THIS ORDER:\n\n"
            "1. OPERATIONAL DEFINITION OF FAILURE. What, concretely, counts "
            "as a model 'failing' to select an appropriate visual form? Be "
            "specific enough that two different people scoring the same "
            "output would agree whether it's a failure. Distinguish this "
            "from 'a form I personally wouldn't have chosen' -- the "
            "criterion must be defensible, not aesthetic.\n\n"
            "2. THE FOUR INTERVENTIONS, FULLY OPERATIONALIZED. For each, "
            "specify exactly what changes in the prompt/context, what stays "
            "held constant, and what the dependent variable is:\n"
            "   - ABLATION: audience and goal context removed entirely. "
            "Specify exactly what 'entirely' means -- what's the minimal "
            "remaining task description?\n"
            "   - CORRUPTION: a FALSE audience premise supplied. Specify how "
            "the false premise is constructed so it's plausible, not "
            "obviously wrong (a model catching an implausible lie isn't "
            "informative).\n"
            "   - ORDER: form commitment forced before vs. after reasoning. "
            "Specify the exact prompting mechanism for each order.\n"
            "   - SUPPLY: an explicit audience->goal->form decision "
            "framework handed to the model. Specify what the framework "
            "actually contains -- this can't be hand-wavy, since H1's "
            "entire test rests on whether THIS specific framework closes "
            "the gap.\n\n"
            "3. THE CEILING CONDITION (required, makes H0 falsifiable per "
            "Backlog #23's own text). Specify exactly what 'maximal "
            "support' means operationally: the framework from SUPPLY, plus "
            "full audience and goal detail, plus the model shown its own "
            "rendered output, plus how many attempts count as 'multiple.' "
            "State precisely what result would count as H0 surviving even "
            "this condition.\n\n"
            "4. SCENARIO DESIGN CONSTRAINTS. Per Naledi's Sprint 7 "
            "culturally-scripted-scenario finding: scenarios must not be "
            "recognizable professional scripts (no finance audits, no VP "
            "status checks) a model could pattern-match rather than reason "
            "through. Specify concrete criteria for what makes a scenario "
            "'non-scripted enough.' Also specify how NOVEL-CONTEXT "
            "conditions get built in (per Bangalore & Stent's grounding, "
            "Sprint 12) -- scenarios where neither shared convention nor an "
            "individually-learned habit cleanly predicts the answer.\n\n"
            "5. MEASUREMENT-ITEM DESIGN. Per Danescu's grounding (Sprint "
            "12): specify how the instrument accounts for positional/"
            "compositional sensitivity within items -- i.e. what varies "
            "within a single scenario's presentation that could itself "
            "shift a score independent of the actual manipulation.\n\n"
            "6. GROUND-TRUTH CONVERGENCE CHECK (required, makes H6 testable "
            "without human readers). Specify the actual procedure: how many "
            "models, how many reruns each, what counts as 'convergence,' "
            "and what happens to the study's interpretation if convergence "
            "is low (i.e. if models/authorities don't even agree with each "
            "other, what does a 'failure' verdict even mean?). Your own "
            "prior-art check flagged a retrieval gap here -- VizML/Draco-"
            "style visualization-recommendation baselines weren't "
            "surfaced. Note explicitly whether this protocol needs them or "
            "can proceed without, and if the former, flag it as a blocking "
            "dependency rather than silently proceeding.\n\n"
            "7. K1A VS K1B AS AN OBSERVATION DIMENSION (backlog #37 -- not "
            "to be resolved here, but must be structurally anchored so "
            "results can be read through it later). For each intervention, "
            "state whether a 'failure' result would be more naturally read "
            "as K1a (the medium/substrate can't express the needed form) or "
            "K1b (the model's generation is unreliable regardless of "
            "substrate) -- or whether the intervention as designed cannot "
            "distinguish them, in which case say that plainly rather than "
            "pretend it can.\n\n"
            "8. WHAT A REGISTRAR NEEDS FROM YOU. You will hand this "
            "protocol to a temporary Registrar role who pre-registers "
            "directional predictions BEFORE Phase 1 piloting. Make sure "
            "everything above is concrete enough for someone with no "
            "further context to write a falsifiable prediction from it "
            "alone.\n\n"
            f"=== BACKLOG #23, FULL TEXT ===\n{backlog_23['description'] if backlog_23 else '(missing)'}\n\n"
            f"=== BACKLOG #37 (K1a/K1b gap) ===\n{backlog_37['description'] if backlog_37 else '(missing)'}\n\n"
            f"=== YOUR PRIOR-ART CHECK ===\n{prior_art[:6000]}\n\n"
            f"=== SPRINT 12 SYNTHESIS (H6 null result, design notes) ===\n{sprint12_synthesis[:6000]}\n"
        )}],
    ) as stream:
        resp = stream.get_final_message()

    protocol = resp.content[0].text
    db.log_usage("kenji", resp.usage.input_tokens, resp.usage.output_tokens)

    db.set_memory("kenji", "sprint13_phase0_protocol", protocol)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"brief-task-{task_id}",
        text=protocol,
        metadata={"agent": "kenji", "type": "sprint13_phase0_protocol"},
    )
    db.update_task(
        task_id, status="completed", result=protocol,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/sprint13_phase0_protocol"},
    )

    print(f"[{NAME}]\n\n{protocol}")
    print(f"\n\n--- {len(protocol)} chars, stored as kenji/sprint13_phase0_protocol ---")


if __name__ == "__main__":
    run()
