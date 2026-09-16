"""Sprint 13, Phase 0 gate -- Ingrid reviews Kenji's protocol before the
Registrar is allowed to pre-register anything.

Scope narrowed by the founder, 2026-09-16: BASELINE + ORDER only for this
sprint (no external rater recruitment yet); AUDIENCE and GOAL deferred to a
follow-up sprint. Two decisions were explicitly handed to Ingrid rather
than left to Kenji or resolved by default: the statistical analysis plan
(Gap 3) and whether reasoning-quality is a pre-registered secondary outcome
(Gap 4, jointly with Sophie -- Sophie's stated pre-position: pre-register
it, but in its own scoring slot so it can't contaminate the Blind Scorer's
primary form-match judgment).
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")

    protocol = db.get_memory("kenji", "sprint13_phase0_protocol") or "(missing)"

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Sprint 13, Phase 0 gate: protocol review + Gaps 3/4 decisions",
        description="Registrar cannot start pre-registration until this gate passes.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Gate review before the Registrar is allowed to pre-register "
            "anything. Founder narrowed scope to BASELINE + ORDER only "
            "(AUDIENCE/GOAL deferred, no rater recruitment this sprint) and "
            "confirmed 3 models: claude-sonnet-4-6, gpt-5.2, gemini-flash-"
            "latest -- the same three used in every prior behavioral sprint "
            "(6, 7, the Gemini addition).\n\n"
            "CHECK, IN ORDER:\n\n"
            "1. PROTOCOL COMPLETENESS FOR BASELINE + ORDER SPECIFICALLY. "
            "Kenji's protocol covers all 4 conditions -- verify BASELINE and "
            "ORDER are each operationalized precisely enough to execute "
            "(exact prompt construction, held-constant elements, dependent "
            "variable) without needing anything from the AUDIENCE/GOAL "
            "sections. Flag if narrowing scope leaves any BASELINE/ORDER-"
            "relevant detail underspecified because it was written assuming "
            "all four conditions would run together.\n\n"
            "2. GROUND-TRUTH ADEQUACY FOR THE NARROWED SCOPE. Kenji's own "
            "verdict: algorithmic consensus (VizML/Draco/Voyager) IS "
            "sufficient for BASELINE and ORDER, human raters are NOT needed "
            "for these two. Verify this claim against what he actually "
            "wrote about those tools' limitations (Section 6.2 of his "
            "protocol) rather than accepting the summary -- does the "
            "narrowed scope genuinely sidestep the rater dependency, or is "
            "there a residual gap even for these two conditions?\n\n"
            "3. K1A/K1B READ FOR THE NARROWED SCOPE. Kenji's summary table: "
            "BASELINE is undistinguishable without a knowledge-elicitation "
            "probe that doesn't exist in the protocol; ORDER reads cleanly "
            "as K1a, conditional on BASELINE passing. Is a study that can "
            "only produce one clean K1a/K1b-relevant result (ORDER) and one "
            "structurally ambiguous one (BASELINE) still worth running as "
            "designed, or does backlog #37's question deserve the missing "
            "elicitation probe added now rather than deferred silently?\n\n"
            "4. GAP 3 -- DECIDE THE STATISTICAL ANALYSIS PLAN. Design: 3 "
            "models x 2 conditions (BASELINE, ORDER) x ~20 scenarios, "
            "within-scenario comparison, binary form-match outcome, plus "
            "the reliability sub-sample (n=4, ICC>=0.75) and the ORDER-"
            "BEFORE positional confound Kenji already disclosed. Specify: "
            "the actual test (e.g. McNemar's for the paired BASELINE-vs-"
            "ORDER binary comparison per model; how model is handled -- "
            "pooled, or as a factor in a mixed-effects model given only 3 "
            "levels), the unit of analysis, and how the 3-models x "
            "1-comparison structure should or shouldn't be corrected for "
            "multiple comparisons. State it precisely enough that it can be "
            "written into the pre-registration verbatim -- this decision is "
            "yours, not a suggestion for Kenji to refine later.\n\n"
            "5. GAP 4 -- REASONING-QUALITY AS SECONDARY OUTCOME. Sophie's "
            "pre-position: pre-register it, but in its own scoring slot so "
            "it can't contaminate the Blind Scorer's primary form-match "
            "judgment. Confirm or overrule, with reasoning. If confirmed, "
            "specify the rating scale and scoring procedure concretely "
            "enough for the Registrar to write a falsifiable prediction "
            "about it (or explicitly rule it exploratory-only if you decide "
            "against pre-registering it).\n\n"
            "6. GATE VERDICT. PROCEED (Registrar may start), REVISE (name "
            "exactly what Kenji must fix first), or BLOCKED (something is "
            "fundamentally wrong with the narrowed design). Be direct -- "
            "the Registrar's predictions get locked once written and cannot "
            "be revised after, so anything wrong with the protocol needs to "
            "surface now, not after pre-registration.\n\n"
            f"=== KENJI'S PHASE 0 PROTOCOL (FULL) ===\n{protocol}\n"
        )}],
    ) as stream:
        response = stream.get_final_message()

    gate = response.content[0].text
    db.log_usage("ingrid", response.usage.input_tokens, response.usage.output_tokens)

    if response.stop_reason == "max_tokens":
        gate += "\n\n[TRUNCATED -- hit max_tokens, response is incomplete.]"

    db.set_memory("ingrid", "sprint13_phase0_gate", gate)
    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"review-task-{task_id}",
        text=gate,
        metadata={"agent": "ingrid", "type": "sprint13_phase0_gate"},
    )
    db.update_task(
        task_id, status="completed", result=gate,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/sprint13_phase0_gate"},
    )

    print(f"[{NAME}]\n\n{gate}")
    print(f"\n\n--- {len(gate)} chars, stored as ingrid/sprint13_phase0_gate ---")


if __name__ == "__main__":
    run()
