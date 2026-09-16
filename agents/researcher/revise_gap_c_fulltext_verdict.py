"""Kenji applies Ingrid's three revisions to the Gap C full-text verdict.

Targeted text revision, not new research -- same practice as every prior
revision in this project (original preserved at a `_v1` key, the revised text
becomes the new current version, spot-checked rather than re-reviewed from
scratch for precision-only fixes).
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))


def run() -> None:
    require_tool("kenji", "write_brief")
    original = db.get_memory("kenji", "gap_c_fulltext_verdict") or ""
    review = db.get_memory("ingrid", "gap_c_fulltext_review") or ""

    if not original or not review:
        raise RuntimeError("Missing original brief or Ingrid's review -- run those first.")

    db.set_memory("kenji", "gap_c_fulltext_verdict_v1", original)

    task_id = db.create_task(
        created_by="ingrid",
        assigned_to="kenji",
        title="Revise Gap C full-text verdict per Ingrid's review",
        description="Apply her three specific revisions -- targeted text fix, not new research.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            f"Your original brief:\n\n{original}\n\n"
            f"Ingrid's full review:\n\n{review}\n\n"
            "Apply her three revisions. This is a targeted text revision, not "
            "new research or new retrieval:\n\n"
            "1. (Required, Section 3) Replace the sentence 'Munzner's later "
            "nested model names audience at the domain level' with a version "
            "correctly scoped to the excerpt, matching the discipline you "
            "already held in Section 2 (e.g. 'the excerpt shows a nested "
            "model where audience appears at the domain level'). Also fix "
            "Section 5's 'chapter on the nested model' framing the same way "
            "-- you don't know these are chapters, only that the excerpt "
            "surfaces this content; relabel the section as provisional "
            "reading targets based on excerpt content, not a priority order "
            "implying knowledge of the book's structure.\n\n"
            "2. (Required, Section 4) Replace the inference chain. Your "
            "original framing treats 'informal training data that discusses "
            "audience explicitly' as one of three equally-weighted candidate "
            "sources for a hypothetical Backlog #23 finding of audience-"
            "sensitive form selection, and frames the source as mysterious "
            "and 'worth tracing.' Ingrid's point: that framing sets up a "
            "false puzzle. The vastly more probable explanation is the "
            "enormous volume of informal discourse (tutorials, journalism, "
            "design blogs, Stack Overflow, UX writing) that discusses "
            "audience constantly and makes up far more of any model's "
            "training data than Mackinlay's formal academic lineage. State "
            "that plainly as the leading candidate, not an afterthought. The "
            "correct, narrower claim your evidence actually supports is: "
            "Mackinlay's formal criteria don't encode audience, so audience "
            "sensitivity (if found) did not come from FORMALIZING his "
            "criteria -- it says nothing about whether the source is "
            "mysterious, because it almost certainly isn't. Reframe what "
            "this means for interpreting Backlog #23: the test is whether "
            "informal training produces RELIABLE internalization versus "
            "pattern-matching, not whether the source itself is unclear.\n\n"
            "3. (Recommended, Section 1 Mackinlay verdict) Add the 'as "
            "operationalized' hedge Ingrid specifies: the formal criteria as "
            "OPERATIONALIZED in APT and its lineage don't model audience, "
            "and note explicitly that Mackinlay named this gap himself in "
            "his own Discussion section -- a scoped omission he was aware "
            "of, not a conceptual blind spot nobody noticed. This is a more "
            "accurate and more useful framing for judging what later systems "
            "did or didn't inherit.\n\n"
            "Leave everything else -- the Mackinlay evidence work, the "
            "excerpt content summary, the retrieval log, sections 2's "
            "caveat discipline -- exactly as it was; Ingrid confirmed those "
            "parts are sound. Output the complete revised brief."
        )}],
    ) as stream:
        resp = stream.get_final_message()

    revised = resp.content[0].text
    db.log_usage("kenji", resp.usage.input_tokens, resp.usage.output_tokens)

    db.set_memory("kenji", "gap_c_fulltext_verdict", revised)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"gap-c-verdict-revised-task-{task_id}",
        text=revised,
        metadata={"agent": "kenji", "type": "gap_c_fulltext_verdict_revised"},
    )
    db.update_task(
        task_id, status="completed", result=revised,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/gap_c_fulltext_verdict"},
    )

    print(f"[{NAME}] Revised Gap C verdict:\n\n{revised}")
    print(f"\n\n--- {len(revised)} chars, stored as kenji/gap_c_fulltext_verdict (v1 preserved) ---")


if __name__ == "__main__":
    run()
