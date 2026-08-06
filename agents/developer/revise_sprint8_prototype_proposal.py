"""Applies Ingrid's corrections to Mateo's Sprint 8 first-prototype
proposal. 3 must-fix architectural specification gaps + 6 same-batch fixes,
before any code gets written.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.developer.persona import NAME, SYSTEM_PROMPT
from agents.permissions import require_tool
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))


def run() -> None:
    require_tool("mateo", "write_task_artifact")
    original = db.get_memory("mateo", "sprint8_prototype_proposal") or ""
    review = db.get_memory("ingrid", "sprint8_prototype_proposal_review") or ""

    if not original or not review:
        raise RuntimeError("Missing original proposal or Ingrid's review -- run those first.")

    db.set_memory("mateo", "sprint8_prototype_proposal_v1", original)

    task_id = db.create_task(
        created_by="ingrid",
        assigned_to="mateo",
        title="Revise Sprint 8 prototype proposal per Ingrid's review",
        description="Resolve 3 must-fix architectural gaps + 6 same-batch fixes before any code is written.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Your original proposal:\n\n{original}\n\n"
                    f"Ingrid's full review:\n\n{review}\n\n"
                    "This is architecture specification work, not new "
                    "research -- resolve these before a single line of code "
                    "gets written:\n\n"
                    "MUST FIX:\n"
                    "1. Stage 2 data sourcing: commit to Path A (LLM-"
                    "synthesized chart data, clearly labeled illustrative/"
                    "not-grounded-in-live-retrieval in the output itself) "
                    "for v1. Defer real search-based retrieval to v2 "
                    "explicitly. Remove the either/or framing entirely.\n\n"
                    "2. Stage 3 context model: specify what the object "
                    "passed between sequentially-written sections actually "
                    "contains. It cannot be prior prose alone -- it needs "
                    "the Stage 2 visual specs (so the writer can accurately "
                    "describe what a chart does), plus whatever navigation/"
                    "interaction state has already been established. Sketch "
                    "this as a rough object shape (a few named fields is "
                    "enough), and stop calling this 'the same discipline, "
                    "different writer' -- it's the same discipline, "
                    "different context model.\n\n"
                    "3. Intermediate representation: sketch a rough schema "
                    "(field-level, doesn't need to be complete) for the "
                    "structured representation the pipeline produces before "
                    "any renderer touches it. State explicitly that Stage 4 "
                    "consumes this representation rather than generating "
                    "HTML directly, so a future non-HTML renderer is "
                    "actually possible later without rewriting stages 1-3.\n\n"
                    "SAME BATCH:\n"
                    "4. Add one explicit paragraph naming where Vega-Lite/"
                    "HTML sits relative to design principle #4's full "
                    "ambition (zoom-as-navigation, motion, true multi-"
                    "dimensional/spatial views) -- own this as a conscious, "
                    "justified first step, not an implied one.\n\n"
                    "5. Reframe the Backlog #9 byproduct test: Vega-Lite "
                    "validation failure rate measures spec syntax/schema "
                    "conformance (an engineering reliability question), NOT "
                    "principled-vs-confabulated reasoning (a semantic "
                    "appropriateness question) -- a spec can be syntactically "
                    "perfect and still reflect a confabulated form choice, "
                    "or fail validation for reasons unrelated to reasoning "
                    "quality. Keep the measurement (it's cheap and useful), "
                    "relabel it as a Stage 2 reliability check, not Backlog "
                    "#9 evidence.\n\n"
                    "6. Add 3-5 explicit, falsifiable pass/fail success "
                    "criteria for v1 (e.g. 'the HTML file opens in a browser "
                    "with zero console errors,' 'the Vega-Lite spec renders "
                    "without validation failure,' 'every visual referenced "
                    "in the prose has a corresponding spec').\n\n"
                    "7. Require explicit audience/goal input for v1 (user "
                    "must state it, not have it inferred) -- defer implicit "
                    "extraction to v2, so a v1 failure is diagnosable to the "
                    "right stage.\n\n"
                    "8. Either cite real evidence for the GPT-4o-for-visual-"
                    "specs default, or explicitly flag it as an untested "
                    "assumption to be validated during v1 (not stated as "
                    "settled fact based on 'experience').\n\n"
                    "9. Add a short closing paragraph stating what DSR "
                    "hypothesis this v1 prototype is actually testing, and "
                    "what outcome would cause the team to revise the "
                    "architecture vs. extend it as-is.\n\n"
                    "Keep everything else -- the TVIR reuse/rebuild table, "
                    "the output-medium call itself (Ingrid confirmed it's "
                    "defensible), the overall stage structure. Output the "
                    "complete revised proposal."
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    revised = response.content[0].text
    db.log_usage("mateo", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="developer_memory",
        doc_id=f"sprint8-prototype-proposal-revised-task-{task_id}",
        text=revised,
        metadata={"agent": "mateo", "type": "sprint8_prototype_proposal_revised"},
    )
    db.set_memory("mateo", "sprint8_prototype_proposal", revised)
    db.update_task(
        task_id, status="completed",
        result="Revision applied; see mateo/sprint8_prototype_proposal.",
        artifact_type="proposal",
        artifact_payload={"memory_key": "mateo/sprint8_prototype_proposal"},
    )

    print(f"[{NAME}] Revised Sprint 8 prototype proposal:\n\n{revised}")


if __name__ == "__main__":
    run()
