"""Sprint 6 follow-up: closes the Gemini gap explicitly flagged in the
original behavioral reasoning test (no Google API key existed at the time).
Re-runs all 6 variants against Gemini and has Naledi fold the results into
the existing brief in place -- this is documented as part of Sprint 6, not
a new sprint, since it closes a gap Sprint 6 itself raised. The prior
2-model version is preserved at naledi/behavioral_reasoning_test_pre_gemini
for an honest record of what changed and when.
"""
import os
import time

from dotenv import load_dotenv
from anthropic import Anthropic
from google import genai
from google.genai import errors as genai_errors

from agents.permissions import require_tool
from agents.researcher_visual.behavioral_reasoning_test import (
    PROMPT_TEMPLATE,
    SCENARIO_PAIRS,
)
from agents.researcher_visual.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

GEMINI_MODEL = "gemini-flash-latest"


def _call_gemini(client: genai.Client, content: str, audience: str, goal: str) -> str:
    prompt = PROMPT_TEMPLATE.format(content=content, audience=audience, goal=goal)
    last_error = None
    for attempt in range(6):
        try:
            response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
            return response.text
        except genai_errors.ServerError as e:
            last_error = e
            time.sleep(5 * (attempt + 1))
        except genai_errors.ClientError as e:
            # Free-tier rate limit (429) -- back off longer than the
            # server-error case; the API's own retryDelay is ~20s.
            if e.code != 429:
                raise
            last_error = e
            time.sleep(25 * (attempt + 1))
    raise last_error


def run() -> None:
    require_tool("naledi", "write_cognitive_annotation")
    db.set_memory("naledi", "status", "online")

    # If a prior Gemini-addition attempt already ran (e.g. Ingrid required
    # revision), the clean 2-model original is preserved at *_pre_gemini --
    # use that as the base, not the flawed 3-model draft, and don't
    # re-clobber the preserved original on a second attempt.
    preserved_original = db.get_memory("naledi", "behavioral_reasoning_test_pre_gemini")
    if preserved_original:
        original_brief = preserved_original
    else:
        original_brief = db.get_memory("naledi", "behavioral_reasoning_test") or ""
        if not original_brief:
            raise RuntimeError("No existing behavioral_reasoning_test brief found -- run the original script first.")
        db.set_memory("naledi", "behavioral_reasoning_test_pre_gemini", original_brief)

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="naledi",
        title="Sprint 6 follow-up: add Gemini to behavioral reasoning test",
        description="Closes the Gemini gap flagged in the original Sprint 6 pilot now that a Google API key exists.",
    )

    gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    gemini_results = []
    for pair in SCENARIO_PAIRS:
        for variant in pair["variants"]:
            content = variant.get("content", pair.get("shared_content"))
            audience = variant["audience"]
            goal = variant["goal"]
            gemini_answer = _call_gemini(gemini_client, content, audience, goal)
            time.sleep(13)  # stay under the free tier's ~5 requests/minute
            gemini_results.append(
                {
                    "pair_id": pair["pair_id"],
                    "varies": pair["varies"],
                    "label": variant["label"],
                    "content": content,
                    "audience": audience,
                    "goal": goal,
                    "gemini_answer": gemini_answer,
                }
            )

    gemini_data_text = ""
    for r in gemini_results:
        gemini_data_text += (
            f"\n=== Pair {r['pair_id']} ({r['varies']}) — {r['label']} ===\n"
            f"CONTENT: {r['content']}\nAUDIENCE: {r['audience']}\nGOAL: {r['goal']}\n\n"
            f"--- Gemini ({GEMINI_MODEL}) response ---\n{r['gemini_answer']}\n"
        )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Your existing Sprint 6 brief (2-model version, Claude + "
                    "GPT, already reviewed and revised per Ingrid) is below, "
                    "followed by Gemini's real responses to the exact same 6 "
                    "scenario variants. Your job: fold Gemini in as a third "
                    "model across the whole brief. This is a real update, "
                    "not a cosmetic one -- rework the content properly:\n\n"
                    "1. Update the scope declaration: Gemini is no longer "
                    "excluded. State plainly that this closes the gap "
                    "flagged in the original pilot, and that it was added "
                    "as a follow-up once a Google API key became available "
                    "-- don't obscure that this happened in two steps.\n\n"
                    "2. In EVERY pair's 'WHAT THE EVIDENCE SHOWS' analysis, "
                    "add Gemini's form choice and reasoning alongside Claude "
                    "and GPT's existing analysis -- same standard: quote "
                    "specific evidence, note whether its reasoning tracks "
                    "the manipulated variable or stays templated, and how it "
                    "compares to the other two models' behavior on that same "
                    "variant.\n\n"
                    "3. Update each pair's verdict to a three-model "
                    "comparison, keeping the existing discipline that these "
                    "verdicts are provisional/single-run, not general model-"
                    "class claims.\n\n"
                    "4. Update 'WHAT THIS MIGHT IMPLY' and your direct "
                    "answer to Ingrid's Sprint 4 question to reflect the "
                    "now-3-model picture. Keep the same honesty about small "
                    "sample size (still only 1 run per model per variant) "
                    "and keep the framing that this remains directional "
                    "evidence, not a quantifiable probability -- do not "
                    "reintroduce a confidence percentage.\n\n"
                    "5. Revisit the Sprint 7 adversarial-pairs probe design: "
                    "note whether having a 3rd model changes anything about "
                    "that design (e.g. worth running the adversarial pairs "
                    "across all 3 models now that all 3 are available).\n\n"
                    "6. Keep the appendix of raw responses, extended to "
                    "include Gemini's raw answers for all 6 variants, IN "
                    "FULL -- do not truncate or summarize any response.\n\n"
                    "This is a second attempt after Ingrid's review of a "
                    "first draft found real problems. Apply these fixes "
                    "specifically:\n\n"
                    "A. The first draft left a visible self-correction in "
                    "the text (confusing which model recommended the A1 "
                    "waterfall chart -- it was Gemini, not Claude). Proofread "
                    "carefully and do not leave any such artifact in.\n\n"
                    "B. The first draft introduced a Claude failure-mode "
                    "label ('over-trust-in-convention') that was weakly "
                    "evidenced and partly caused by the misattribution in "
                    "(A). Do NOT introduce a named failure-mode label for "
                    "Claude in this brief -- Claude's A1/A2 responses in "
                    "this dataset are the most defensible in the set. If you "
                    "want to note an open question about Claude for Sprint "
                    "7, frame it as 'does Claude's correct A2 prose choice "
                    "generalize?' -- a question, not a failure-mode claim.\n\n"
                    "C. Keep 'form-conservatism' (Gemini, Pair B) hedged as "
                    "a pattern/candidate label EVERYWHERE it appears -- "
                    "including the synthesis and the direct answer to "
                    "Ingrid's question, not just at the pair-verdict level. "
                    "It's grounded in one pair (2 variants), say so every "
                    "time you use the label.\n\n"
                    "D. Be internally consistent about Gemini's A2 "
                    "flowchart: your Pair A analysis correctly notes "
                    "flowcharts require reading node-link structure and "
                    "inferring directionality, which is its own form of "
                    "interpretive burden. Don't then list the A2 flowchart "
                    "as an unqualified 'stronger case' in the synthesis "
                    "alongside Claude's prose and GPT's heatmap -- keep the "
                    "nuance (better than GPT's chart-for-a-narrative-"
                    "audience choice, but not as clean a case as the other "
                    "two) consistent throughout.\n\n"
                    f"YOUR EXISTING BRIEF:\n\n{original_brief}\n\n"
                    f"GEMINI'S RAW RESPONSES (real API calls, not simulated):\n{gemini_data_text}\n\n"
                    "Output the complete updated brief."
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    updated_brief = response.content[0].text
    db.log_usage("naledi", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"behavioral-reasoning-test-gemini-added-task-{task_id}",
        text=updated_brief,
        metadata={"agent": "naledi", "type": "behavioral_reasoning_test_gemini_added"},
    )
    db.set_memory("naledi", "behavioral_reasoning_test", updated_brief)
    db.update_task(
        task_id, status="completed",
        result="Gemini added as third model; see naledi/behavioral_reasoning_test.",
        artifact_type="research_brief",
        artifact_payload={"memory_key": "naledi/behavioral_reasoning_test"},
    )

    print(f"[{NAME}] Gemini added to behavioral reasoning test:\n\n{updated_brief}")


if __name__ == "__main__":
    run()
