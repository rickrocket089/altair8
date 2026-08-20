"""Sophie revises Pass 4 against Ingrid's mark check.

Verdict was MARKING NOT HONEST. Seven unmarked sentences that are Sophie's own
observations, two mildly over-marked (conservative, no fix required), and one
substantive omission: the C3 block dropped Kenji's explicit caveat that his
verdict "rests partly on recollection" for Bertin and Munzner, which were never
retrieved as primary documents. That omission made the sprint's most severe
verdict read as better grounded than the retrieval log supports.

The mechanism worked. Pass 4's only external check found something real on its
first use, and it found it in Section 3 -- exactly where Ingrid predicted an
unmarked characterisation would be easiest to smuggle in as fact.

v1 preserved at team_leader/sprint10_synthesis_v1.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.team_leader.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))


def run() -> None:
    require_tool("team_leader", "read_all")
    db.set_memory("team_leader", "status", "online")

    synthesis = db.get_memory("team_leader", "sprint10_synthesis") or ""
    check = db.get_memory("ingrid", "sprint10_synthesis_mark_check") or ""
    if not synthesis or not check:
        raise SystemExit("Missing synthesis or mark check.")

    if not db.get_memory("team_leader", "sprint10_synthesis_v1"):
        db.set_memory("team_leader", "sprint10_synthesis_v1", synthesis)
        print(f"[{NAME}] v1 preserved at team_leader/sprint10_synthesis_v1")
    else:
        print(f"[{NAME}] _v1 already exists — not overwriting (rerun-safe).")

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="team_leader",
        title="Sprint 10 Pass 4 revision: apply Ingrid's mark check",
        description="Seven marks added, C3 recollection caveat restored.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Ingrid checked your Pass 4 marking and returned MARKING NOT "
            "HONEST. Revise.\n\n"
            "Reproduce the synthesis in full with her required fixes applied "
            "and NOTHING ELSE CHANGED. Do not improve the prose, restructure "
            "the sections, or add analysis. This is a correction pass -- any "
            "change beyond her list is out of scope and makes the revision "
            "harder to verify.\n\n"
            "The three required fixes:\n\n"
            "1. MOST IMPORTANT. In the C3 block of Section 3, restore Kenji's "
            "explicit caveat that his verdict on the selection-mechanism claim "
            "rests partly on recollection for Bertin's Semiologie Graphique "
            "and Munzner's nested model, neither of which was retrieved as a "
            "primary document. Your current text presents C3's Category C "
            "verdict as more firmly grounded than his retrieval log supports. "
            "APT itself WAS retrieved and that part stands -- do not weaken "
            "it. The caveat applies to the wider grammar-tradition claim.\n\n"
            "2. Mark these seven sentences with [SOPHIE]:\n"
            "   - 'C3 and C6 build artifacts calibrated to the information or "
            "domain itself, with the reader as secondary.'\n"
            "   - 'All five Pass 1 concepts route human control through "
            "natural language.'\n"
            "   - The 'more urgent restatement requirement' sentence for C2 "
            "(see fix 3).\n"
            "   - In Section 3's C3 block: 'The concept cannot be presented "
            "without full reframing that engages explicitly with this prior "
            "art.'\n"
            "   - In Section 3's C1 block: the packaging of the restated claim "
            "('state the concept's contribution specifically as: continuous "
            "confidence scoring...').\n"
            "   - In Section 4's C4 block: 'The concept by design requires "
            "pairing with other concepts if the team's goal is to serve the "
            "full goal space.'\n"
            "   - In Section 4's C6 block: 'proceeding to build without that "
            "search means building on an unverified novelty claim'.\n\n"
            "3. For C2, either mark 'more urgent' with [SOPHIE] or drop the "
            "comparative. As written it implies Kenji ranked C2's restatement "
            "need above C1's. He did not.\n\n"
            "She also found two mildly over-marked sentences and explicitly "
            "required no correction for those -- over-marking is the "
            "conservative direction. Leave them.\n\n"
            "=========== HER CHECK ===========\n"
            f"{check}\n\n"
            "=========== YOUR SYNTHESIS TO REVISE ===========\n"
            f"{synthesis}\n\n"
            "Output the complete revised synthesis. No preamble, no summary of "
            "what you changed -- just the document."
        )}],
    ) as stream:
        response = stream.get_final_message()

    revised = response.content[0].text
    db.log_usage("team_leader", response.usage.input_tokens, response.usage.output_tokens)

    marks = revised.count("[SOPHIE]")
    has_caveat = "recollection" in revised.lower()
    print(f"[{NAME}] Revised: {len(revised)} chars, {marks} marks "
          f"(was 11). C3 recollection caveat present: {has_caveat}")

    db.set_memory("team_leader", "sprint10_synthesis", revised)
    vectorstore.remember(
        collection_name="team_leader_memory",
        doc_id=f"sprint10-pass4-v2-task-{task_id}",
        text=revised,
        metadata={"agent": "team_leader", "type": "sprint_synthesis", "sprint": 10, "version": 2},
    )
    db.update_task(
        task_id, status="completed", result=revised,
        artifact_type="sprint_synthesis",
        artifact_payload={
            "memory_key": "team_leader/sprint10_synthesis",
            "version": 2,
            "sophie_marks": marks,
        },
    )
    print(f"[{NAME}] v2 stored at team_leader/sprint10_synthesis.")


if __name__ == "__main__":
    run()
