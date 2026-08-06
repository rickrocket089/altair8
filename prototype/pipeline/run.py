"""Sprint 8 prototype -- end-to-end orchestrator for the 4-stage pipeline.

Usage: docker compose run --rm agents python -m prototype.pipeline.run

Runs Planner -> Visual Asset Generator -> Component Writer -> HTML Renderer
against a fixed example request (v1 requires explicit audience/goal input,
no CLI parsing yet -- that's an intentional v1 scope cut, not an oversight).

After rendering, checks what it can of the 5 success criteria from the
approved Sprint 8 proposal automatically, and reports the rest for manual
verification (criteria 1 and 4 need a real browser / human judgment).
"""
import os

from prototype.pipeline import content_grounding, planner, renderer, visual_asset_generator, writer
from prototype.pipeline.schema import PipelineDocument, SectionNode

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

REQUEST = "Summarize the state of urban heat island mitigation techniques."
AUDIENCE = "A city council making a budget decision in the next 30 days."
GOAL = "Help them allocate budget between three mitigation approaches."

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "workspace", "outputs", "prototype-runs")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "sprint8-v1-run1.html")


def run() -> None:
    print("=== Stage 1: Planning ===")
    plan = planner.plan(REQUEST, AUDIENCE, GOAL)
    print(f"Planned {len(plan['sections'])} sections: {[s['title'] for s in plan['sections']]}")

    doc = PipelineDocument(title=plan["title"], audience=AUDIENCE, goal=GOAL)
    prior_context: list[dict] = []

    for sec_plan in plan["sections"]:
        sec_id = sec_plan["id"]
        print(f"\n=== Section '{sec_id}' ===")

        visuals = []
        vis_req = sec_plan.get("visual_requirement", {})
        if vis_req.get("needed"):
            print(f"Stage 2: generating visual for '{sec_id}'...")
            slot_id = f"{sec_id}-chart"
            vs = visual_asset_generator.generate_visual(
                slot_id=slot_id,
                content_summary=sec_plan["content_summary"],
                description=vis_req.get("description", ""),
                why=vis_req.get("why", ""),
                interaction=sec_plan.get("suggested_interaction", ""),
            )
            visuals.append(vs)
            status = "OK" if vs.validation_passed else "FAILED VALIDATION"
            print(f"  -> {status} ({vs.generator_model})")
            if not vs.validation_passed:
                doc.global_notes.append(
                    f"Section '{sec_id}': visual generation failed structural validation "
                    f"({vs.generator_model}). Shown as a flagged placeholder, not silently dropped."
                )
            else:
                # Structurally valid -- now check it's actually ABOUT the
                # right topic (a different question, see content_grounding.py)
                print(f"  Checking content grounding for '{sec_id}'...")
                grounding = content_grounding.check_coherence(
                    section_title=sec_plan["title"],
                    content_summary=sec_plan["content_summary"],
                    visual_description=vis_req.get("description", ""),
                    visual_why=vis_req.get("why", ""),
                    spec=vs.spec,
                )
                vs.content_grounded = grounding.get("consistent")
                vs.grounding_issues = grounding.get("issues", [])
                g_status = "GROUNDED" if vs.content_grounded else "OFF-TOPIC"
                print(f"  -> {g_status}: {grounding.get('reasoning', '')}")
                if not vs.content_grounded:
                    doc.global_notes.append(
                        f"Section '{sec_id}': visual passed structural validation but FAILED "
                        f"content-grounding check ({'; '.join(vs.grounding_issues)}). "
                        f"Shown as a flagged placeholder, not silently dropped."
                    )

        print(f"Stage 3: writing '{sec_id}'...")
        written = writer.write_section(
            title=sec_plan["title"],
            content_summary=sec_plan["content_summary"],
            audience_note=sec_plan["audience_note"],
            visuals=visuals,
            prior_sections=prior_context,
            audience=AUDIENCE,
            goal=GOAL,
        )

        section_node = SectionNode(
            id=sec_id,
            title=sec_plan["title"],
            prose_blocks=written["prose_blocks"],
            visual_slots=visuals,
            navigation_anchors=[sec_id],
        )
        doc.sections.append(section_node)

        prior_context.append({
            "title": sec_plan["title"],
            "prose_summary": written["prose_summary"],
            "visual_slot_ids": [v.slot_id for v in visuals],
            "interactions": [sec_plan.get("suggested_interaction")] if sec_plan.get("suggested_interaction") not in (None, "none") else [],
        })

    print("\n=== Stage 4: Rendering ===")
    html_output = renderer.render(doc)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"Written to {OUTPUT_PATH}")

    _report(doc, plan)


def _report(doc: PipelineDocument, plan: dict) -> None:
    print("\n=== Success criteria check (automatable subset) ===")

    all_slots = doc.all_visual_slots()

    c2 = all(v.validation_passed for v in all_slots.values()) if all_slots else True
    print(f"2. All Vega-Lite specs pass structural validation: {'PASS' if c2 else 'FAIL'} "
          f"({sum(1 for v in all_slots.values() if v.validation_passed)}/{len(all_slots)})")

    grounded_checked = [v for v in all_slots.values() if v.validation_passed]
    if grounded_checked:
        n_grounded = sum(1 for v in grounded_checked if v.content_grounded)
        print(f"2b. Content-grounding check (not one of the 5 original criteria, added Sprint 8 "
              f"post-run-1): {n_grounded}/{len(grounded_checked)} structurally-valid charts also "
              f"passed topic coherence")

    c3 = all(len(s.visual_slots) == sum(1 for sp in plan["sections"] if sp["id"] == s.id and sp.get("visual_requirement", {}).get("needed")) for s in doc.sections)
    print(f"3. Every planned visual has a corresponding VisualSlot object: {'PASS' if c3 else 'FAIL'}")

    audience_notes = [sp.get("audience_note", "") for sp in plan["sections"]]
    c5 = all(len(n) > 15 for n in audience_notes)  # crude non-generic/non-empty proxy
    named_decisions = [sp for sp in plan["sections"] if sp.get("visual_requirement", {}).get("needed") and len(sp["visual_requirement"].get("why", "")) > 15]
    print(f"5. Audience/goal traceable: audience_notes populated: {'PASS' if c5 else 'FAIL'}; "
          f"{len(named_decisions)} visual(s) with a substantive audience/goal justification")

    print("\n1. Zero console errors in a real browser: NOT AUTOMATED -- open the file and check manually.")
    print("4. Prose accurately describes chart type/interaction: NOT AUTOMATED -- manual check on first run, per the approved proposal.")

    print(f"\n=== Stage 2 reliability log ===")
    from prototype.pipeline import reliability_log
    print(reliability_log.summarize())

    print("\n=== DSR note ===")
    failed = [n for n in doc.global_notes]
    if failed:
        print(f"{len(failed)} failure(s) logged, all stage-attributable (Stage 2 validation): {failed}")
        print("This is consistent with the hypothesis under test: stage separation localizes failures.")
    else:
        print("No failures this run -- pipeline completed clean end-to-end.")


if __name__ == "__main__":
    run()
