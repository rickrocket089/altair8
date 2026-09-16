"""Sprint 13, Phase 0 amendment: operationalize the knowledge-elicitation
probe Sophie approved (R3, 2026-09-16) to make BASELINE diagnostic between
K1a (application failure) and K1b (knowledge absence) -- backlog #37.

Kenji's own Phase 0 protocol already flagged this as "operationally simple
... a single additional prompt per scenario asking the model to list form
recommendations for the data schema without any communicative task
framing" and said it would require a protocol amendment. This is that
amendment, at the same level of precision as the rest of the protocol --
not a rough sketch.
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

    protocol = db.get_memory("kenji", "sprint13_phase0_protocol") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 13 Phase 0 amendment: operationalize the knowledge-elicitation probe",
        description="Sophie approved adding it (R3, 2026-09-16) -- now precise, protocol-ready.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model=MODEL, max_tokens=4000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Sophie approved adding the knowledge-elicitation probe you "
            "flagged as needed to make BASELINE diagnostic between K1a "
            "(application failure) and K1b (knowledge absence). Her "
            "instruction: the probe runs after form selection, before the "
            "next stimulus, must not contaminate blind scoring (probe "
            "outputs collected separately, deblinded only after the Blind "
            "Scorer's primary pass is complete), and needs its own "
            "directional prediction from the Registrar.\n\n"
            "Write the full amendment, at the same precision level as the "
            "rest of your protocol:\n\n"
            "1. EXACT PROBE PROMPT. The full text of what the model is "
            "asked, verbatim, with zero communicative-task framing (no "
            "audience, no goal, no scenario narrative) -- just the data "
            "schema. Specify exactly what schema information is given (same "
            "schema as the paired BASELINE scenario? confirm).\n\n"
            "2. TIMING AND ISOLATION. Confirm: administered as a separate "
            "call, after the BASELINE form-choice output is already "
            "recorded and sealed, so the probe response cannot retroactively "
            "influence or be influenced by the BASELINE output. Same model, "
            "same scenario's data schema, new conversation context (no "
            "shared context with the BASELINE call, to avoid anchoring).\n\n"
            "3. SCORING. How is a probe response evaluated? Specify: does "
            "the model's listed recommendation(s) need to match the "
            "Layer-1 algorithmic consensus (VizML/Draco/Voyager) established "
            "for that scenario? What counts as a pass (knowledge present) "
            "vs a fail (knowledge absent)? This determines the K1a/K1b "
            "read, so be as precise as the primary failure criterion in "
            "Section 1.\n\n"
            "4. THE DIAGNOSTIC LOGIC, MADE EXPLICIT. Complete this table "
            "for the Registrar:\n"
            "   - Probe PASS + BASELINE PASS -> [what does this mean?]\n"
            "   - Probe PASS + BASELINE FAIL -> [K1a signal: knowledge "
            "present, application failed]\n"
            "   - Probe FAIL + BASELINE FAIL -> [K1b signal: knowledge "
            "absent]\n"
            "   - Probe FAIL + BASELINE PASS -> [this combination would be "
            "strange -- say what it would mean if observed, don't dismiss "
            "it as impossible]\n\n"
            "5. CONTAMINATION-ISOLATION PROCEDURE FOR THE BLIND SCORER. "
            "Sophie's instruction is explicit: probe outputs must not reach "
            "the Blind Scorer until after the primary form-match pass is "
            "complete. Specify the actual mechanism (a separate data file, "
            "a locked record, whatever fits the existing contamination-"
            "prevention procedure Ingrid specified for reasoning-quality "
            "scoring in the gate review) -- don't just assert isolation, "
            "specify how it's enforced.\n\n"
            "6. REGISTRAR HANDOFF. State the directional prediction "
            "structure the Registrar needs to write (e.g. 'X% of BASELINE "
            "failures will show probe PASS, indicating the failure mode is "
            "predominantly K1a not K1b' -- or your own better-justified "
            "direction). Ground the direction in something from the record "
            "if you can (e.g. Sprint 6/7's finding that models show *some* "
            "audience-sensitive reasoning suggests underlying knowledge "
            "often exists) rather than a coin flip.\n\n"
            "Keep this tight -- it's an amendment to an existing protocol, "
            "not a new document. Reference the existing BASELINE section "
            "rather than restating it.\n\n"
            f"=== YOUR EXISTING PHASE 0 PROTOCOL (for reference, includes "
            f"the R1/R2 amendments already applied) ===\n{protocol[-15000:]}\n"
        )}],
    ) as stream:
        resp = stream.get_final_message()

    amendment = resp.content[0].text
    db.log_usage("kenji", resp.usage.input_tokens, resp.usage.output_tokens)
    if resp.stop_reason == "max_tokens":
        amendment += "\n\n[TRUNCATED -- hit max_tokens, incomplete.]"

    full = protocol + "\n\n---\n\n## AMENDMENT: Knowledge-Elicitation Probe (2026-09-16)\n\n" + amendment
    db.set_memory("kenji", "sprint13_phase0_protocol", full)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"brief-task-{task_id}",
        text=amendment,
        metadata={"agent": "kenji", "type": "elicitation_probe_amendment"},
    )
    db.update_task(
        task_id, status="completed", result=amendment,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/sprint13_phase0_protocol"},
    )

    print(f"[{NAME}]\n\n{amendment}")
    print(f"\n\n--- {len(amendment)} chars, appended to kenji/sprint13_phase0_protocol ---")


if __name__ == "__main__":
    run()
