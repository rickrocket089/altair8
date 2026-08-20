"""Mateo checks whether Sprint 10's falsification tests are actually buildable.

Sprint 10 success criterion (b). Deliberately bounded per Ingrid's finding 8:
Mateo sees ONLY field 6 (the falsification test) of each concept, not the full
template, and returns a binary verdict plus one sentence. Full architectural
engagement happens only if a concept is selected.

That bound assumes field 6 is separable from the mechanism in fields 1-2, which
is sometimes false -- a test can be buildable for a simpler proxy than the
concept actually proposes. Ingrid required the caveat be given to Mateo
explicitly rather than left implicit, so "cannot judge without the mechanism"
is an available verdict. It is enforced here by actually withholding fields
1-5 and 7, not by asking him to ignore them.
"""
import os
import re

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.developer.persona import NAME, SYSTEM_PROMPT
from agents.permissions import require_tool
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"


def extract_field_6(text: str) -> list[dict]:
    """Pull each concept's title and its field 6 section only."""
    concepts = []
    titles = list(re.finditer(r"^#\s*CONCEPT\s+(\d+):\s*(.+)$", text, re.MULTILINE))
    for i, match in enumerate(titles):
        start = match.end()
        end = titles[i + 1].start() if i + 1 < len(titles) else len(text)
        body = text[start:end]
        field6 = re.search(
            r"^##\s*6\.\s*WHAT WOULD FALSIFY IT\s*$(.*?)(?=^##\s*7\.|\Z)",
            body, re.MULTILINE | re.DOTALL,
        )
        if field6:
            concepts.append({
                "number": match.group(1),
                "title": match.group(2).strip(),
                "field6": field6.group(1).strip(),
            })
    return concepts


def run() -> None:
    # read_brief, not read_task_artifact -- the latter is Ingrid's permission,
    # not Mateo's. Caught by agents/permissions.py on the first run.
    require_tool("mateo", "read_brief")
    db.set_memory("mateo", "status", "online")

    blind = db.get_memory("priya", "sprint10_concepts_blind") or ""
    concepts = extract_field_6(blind)
    if not concepts:
        raise SystemExit("Could not extract any field 6 sections — check the format.")
    print(f"[{NAME}] Extracted field 6 from {len(concepts)} concepts "
          f"(fields 1-5 and 7 withheld by design).")

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="mateo",
        title="Sprint 10 criterion (b): are the falsification tests buildable?",
        description=f"Field-6-only review of {len(concepts)} concepts, binary verdicts.",
    )

    blocks = "\n\n".join(
        f"--- CONCEPT {c['number']}: {c['title']}\n\n{c['field6']}" for c in concepts
    )

    user_message = f"""Sprint 10 success criterion (b). A short, bounded job.

Five concepts have been proposed for Altair8's communication layer. Each names
an experiment that would falsify it. Your only question, per concept:

  COULD THIS TEST BE BUILT AND RUN WITHIN ROUGHLY ONE SPRINT?

Rules for your verdict:
- Binary: BUILDABLE or NOT BUILDABLE. Plus exactly one sentence of reasoning.
- A test requiring infrastructure this team has not built counts as buildable
  only if that infrastructure could itself be built inside the same sprint.
- Consider what running the test actually requires end to end, including
  recruiting whoever has to look at something, not only the code.

IMPORTANT — you are being shown ONLY the falsification test for each concept.
The concept itself, its mechanism, and its rationale have been deliberately
withheld from you, to keep this review bounded. That withholding has a known
cost: a test can look buildable in isolation while actually testing a simpler
proxy than the concept proposes. So:

  If you cannot evaluate whether this test is buildable without understanding
  the mechanism behind it, say so explicitly in your one sentence rather than
  guessing. "CANNOT JUDGE WITHOUT THE MECHANISM" is a valid verdict and is more
  useful to us than a confident wrong one.

Do not design the tests, improve them, or comment on the concepts. Verdicts only.

{blocks}

End with a one-line tally: how many BUILDABLE, how many NOT BUILDABLE, how many
CANNOT JUDGE."""

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model=MODEL,
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        response = stream.get_final_message()

    verdicts = response.content[0].text
    db.log_usage("mateo", response.usage.input_tokens, response.usage.output_tokens)

    db.set_memory("mateo", "sprint10_buildability", verdicts)
    vectorstore.remember(
        collection_name="developer_memory",
        doc_id=f"sprint10-buildability-task-{task_id}",
        text=verdicts,
        metadata={"agent": "mateo", "type": "buildability_check", "sprint": 10},
    )
    db.update_task(
        task_id, status="completed", result=verdicts,
        artifact_type="buildability_check",
        artifact_payload={
            "memory_key": "mateo/sprint10_buildability",
            "concepts_reviewed": len(concepts),
            "scope": "field 6 only",
        },
    )

    print(f"[{NAME}]\n\n{verdicts}")


if __name__ == "__main__":
    run()
