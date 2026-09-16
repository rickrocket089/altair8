"""Sprint 14 pre-phase: does Sophie's Option 3 (Draco stays a data-conformity
layer, Blind Scorer alone carries audience-optimality) actually satisfy
what Kenji's own Sprint 13 Section 5 specified for the "audience-optimal"
criterion -- or did Section 5 implicitly assume a single, unified ground
truth that splitting into two layers can't provide?

Sophie's framing: 30 minutes of work, not a sprint -- a yes/no with a
concrete reason, gating whether Option 3 proceeds or the team needs to
discuss further.
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

    synthesis = db.get_memory("kenji", "sprint13_synthesis") or ""
    idx = synthesis.find("## 5. WHAT WOULD ACTUALLY TEST")
    section5 = synthesis[idx:idx + 6000] if idx != -1 else synthesis[-6000:]

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 14 pre-phase: does Option 3 satisfy Section 5's audience-optimal criterion?",
        description="Gates whether Sprint 14 proceeds on Option 3 or needs further discussion.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=3000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Sophie's proposed Option 3 for Sprint 14's ground-truth "
            "architecture: Draco stays as a data-structure-conformity "
            "layer only (what it can actually do); the Blind Scorer alone "
            "carries the full audience-optimality judgment (comparing the "
            "model's chosen form against what a human-equivalent judge "
            "considers optimal for the specific audience+goal pairing, "
            "using the rubric and the scenario context -- no Draco "
            "audience input at all).\n\n"
            "Check this against what YOUR OWN Section 5 (below) actually "
            "specified for the audience-optimal criterion. Be precise:\n\n"
            "1. Does Section 5 require a SHARED ground truth that both "
            "'structural validity' and 'audience-optimality' are checked "
            "against, or does it already treat these as two separable "
            "checks that different layers could handle? Quote or closely "
            "paraphrase the specific language that settles this.\n\n"
            "2. The 'rank ordering of structurally valid forms per A x G "
            "pairing' you specified -- does that ranking NEED to come from "
            "an algorithmic tool (Draco or otherwise), or could the Blind "
            "Scorer itself produce a ranked judgment per scenario, "
            "functioning as the entire ground-truth layer for the "
            "audience dimension? If the Blind Scorer can BE the ranking "
            "mechanism, Option 3 works cleanly. If Section 5 assumed the "
            "ranking needed to be independently algorithmic (so it's not "
            "just 'the same LLM judging itself'), that's a real problem "
            "for Option 3 -- say so plainly.\n\n"
            "3. THE SPECIFIC RISK TO CHECK: if the Blind Scorer both "
            "produces the audience-optimal judgment AND scores the model "
            "outputs against it, is there a circularity or self-grading "
            "concern -- the same kind of problem the Registrar role and "
            "the blind-scoring architecture exist to prevent elsewhere in "
            "this project? Does Option 3 reintroduce a version of the "
            "'LLM grades its own kind of output' problem that motivated "
            "building the Blind Scorer role blind in the first place?\n\n"
            "4. VERDICT: does Option 3 satisfy Section 5 as written, with "
            "a specific reason -- or does it not, with a specific gap "
            "named? If it doesn't fully satisfy Section 5, name the "
            "minimal fix (e.g. a separate ranking pass before scoring, "
            "a different judge, an explicit rubric constraint) rather "
            "than just flagging the problem.\n\n"
            f"=== YOUR SPRINT 13 SECTION 5 (verbatim) ===\n{section5}\n"
        )}],
    )

    verdict = result.text
    db.log_usage("kenji", result.input_tokens, result.output_tokens)

    db.set_memory("kenji", "sprint14_option3_check", verdict)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"brief-task-{task_id}",
        text=verdict,
        metadata={"agent": "kenji", "type": "sprint14_option3_check"},
    )
    db.update_task(
        task_id, status="completed", result=verdict,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/sprint14_option3_check"},
    )

    print(f"[{NAME}] (continuations: {result.continuations})\n\n{verdict}")
    print(f"\n\n--- {len(verdict)} chars, stored as kenji/sprint14_option3_check ---")


if __name__ == "__main__":
    run()
