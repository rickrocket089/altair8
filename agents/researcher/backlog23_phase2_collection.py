"""Sprint 13, Phase 2: the full confirmatory data collection.

20 scenarios x (BASELINE, ORDER-BEFORE, PROBE) x 3 models = 180 real API
calls. Prompt construction and audience/goal descriptor text reused
verbatim from Phase 1's pilot (agents/researcher/backlog23_phase1_pilot.py)
-- same functions, same CALL_MAX_TOKENS=2000, same stop_reason/
finish_reason checks that Phase 1 proved were necessary (2 of 27 pilot
calls were silently truncated at the old 600-token ceiling before that fix
landed).

This is the confirmatory run the Registrar's pre-registration and Ingrid's
statistical plan (exact McNemar's per model) apply to -- BASELINE and
ORDER-BEFORE only, per the founder's scope narrowing (AUDIENCE/GOAL
deferred). Sophie's ruling on the Gemini probe-coverage question (2026-09-
16): probe results are scored per-model, not pooled; no model is excluded.
"""
import json
import os
import time

from dotenv import load_dotenv
from anthropic import Anthropic
from openai import OpenAI
from google import genai
from google.genai import errors as genai_errors

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

CLAUDE_MODEL = "claude-sonnet-4-6"
GPT_MODEL = "gpt-5.2"
GEMINI_MODEL = "gemini-flash-latest"
# Real run found this too low for Gemini's BASELINE responses ("reason step
# by step" elicits verbose chain-of-thought before commitment) -- 13/180
# calls truncated at 2000, one needed 8000 before it stopped. Raised the
# default; the per-call retry logic that fixed the real run by hand should
# be treated as the reason this number is 4000 now, not a guess.
CALL_MAX_TOKENS = 4000

TASK_FRAMING = "You are a communication designer preparing a presentation artifact."

AUDIENCE = {
    "A1": "Your audience is familiar with the measurement domain, but unfamiliar with this specific dataset -- they have no prior hypothesis about its shape or direction.",
    "A2": "Your audience has no domain vocabulary, but is accustomed to interpreting quantitative comparisons in everyday contexts (news media, public health communications, consumer reports).",
    "A3": "Your audience monitors this same metric repeatedly over time and holds a stable mental model of its typical range and variability -- their task is anomaly detection against that expectation.",
    "A4": "Your audience will act on the output of a single viewing, under time pressure, without ability to ask follow-up questions.",
    "A5": "Your audience holds a strong prior belief about the expected finding and will scrutinize the chart for evidence consistent or inconsistent with that belief.",
    "A6": "Your audience receives the chart embedded in a larger document and will not read surrounding text before forming a first interpretation.",
}
GOAL = {
    "G1": "Your goal is to help the audience establish whether a directional change over ordered time points is monotonic, interrupted, or cyclical.",
    "G2": "Your goal is to help the audience determine which of several discrete categories has the largest or smallest value on a single measure.",
    "G3": "Your goal is to help the audience understand how values are distributed across a full range, including where the bulk of observations fall and how spread out they are.",
    "G4": "Your goal is to support a binary or multi-option choice by making the decision-relevant difference between options perceptually immediate.",
    "G5": "Your goal is to help the audience identify whether two or more variables move together, independently, or in opposition across observations.",
    "G6": "Your goal is to help the audience verify that a value or set of values falls within or outside a pre-specified acceptable range.",
}


def _baseline_prompt(sc: dict) -> str:
    return (
        f"{TASK_FRAMING}\n\n{sc['data_description']}\n\n"
        f"{AUDIENCE[sc['audience']]}\n\n{GOAL[sc['goal']]}\n\n"
        "Please reason through this step by step. Then specify which visual "
        "form you would use."
    )


def _order_before_prompt(sc: dict) -> str:
    return (
        f"{TASK_FRAMING}\n\n{sc['data_description']}\n\n"
        f"{AUDIENCE[sc['audience']]}\n\n{GOAL[sc['goal']]}\n\n"
        "Before reasoning through this, commit to a visual form. Name the "
        "form in one sentence first. Then explain your reasoning."
    )


def _probe_prompt(sc: dict) -> str:
    return (
        f"Data schema: {sc['data_description']}\n\n"
        "Task: List the visualization form or forms that are most appropriate "
        "for data with this schema. For each form you list, state the "
        "property of the schema that makes it appropriate.\n\n"
        "Respond only with the list. Do not ask clarifying questions. Do not "
        "recommend a specific use case. Do not describe what the chart would "
        "communicate to an audience."
    )


def _call_claude(client: Anthropic, prompt: str) -> str:
    response = client.messages.create(
        model=CLAUDE_MODEL, max_tokens=CALL_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason == "max_tokens":
        raise RuntimeError(f"Claude response truncated at {CALL_MAX_TOKENS} tokens")
    return "\n".join(b.text for b in response.content if b.type == "text")


def _call_gpt(client: OpenAI, prompt: str) -> str:
    response = client.chat.completions.create(
        model=GPT_MODEL, max_completion_tokens=CALL_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    if response.choices[0].finish_reason == "length":
        raise RuntimeError(f"GPT response truncated at {CALL_MAX_TOKENS} tokens")
    return response.choices[0].message.content


def _call_gemini(client: "genai.Client", prompt: str) -> str:
    last_error = None
    for attempt in range(6):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL, contents=prompt,
                config={"max_output_tokens": CALL_MAX_TOKENS},
            )
            finish_reason = getattr(response.candidates[0], "finish_reason", None)
            if getattr(finish_reason, "name", str(finish_reason)) != "STOP":
                raise RuntimeError(f"Gemini response truncated or incomplete: finish_reason={finish_reason}")
            return response.text
        except genai_errors.ServerError as e:
            last_error = e
            time.sleep(5 * (attempt + 1))
        except genai_errors.ClientError as e:
            if e.code != 429:
                raise
            last_error = e
            time.sleep(25 * (attempt + 1))
    raise last_error


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    scenarios = json.loads(db.get_memory("kenji", "sprint13_scenarios_structured"))
    assert len(scenarios) == 20, f"expected 20 scenarios, got {len(scenarios)}"

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 13, Phase 2: full confirmatory data collection (180 calls)",
        description="20 scenarios x BASELINE/ORDER-BEFORE/PROBE x 3 models.",
    )

    claude_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    gpt_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    callers = {
        "claude-sonnet-4-6": lambda p: _call_claude(claude_client, p),
        "gpt-5.2": lambda p: _call_gpt(gpt_client, p),
        "gemini-flash-latest": lambda p: _call_gemini(gemini_client, p),
    }

    raw_results = []
    for scenario_id in sorted(scenarios):
        sc = scenarios[scenario_id]
        for condition, prompt_fn in [
            ("BASELINE", _baseline_prompt),
            ("ORDER-BEFORE", _order_before_prompt),
            ("PROBE", _probe_prompt),
        ]:
            prompt = prompt_fn(sc)
            for model_name, caller in callers.items():
                try:
                    output = caller(prompt)
                    status = "OK"
                except Exception as exc:
                    output = f"(call failed: {exc})"
                    status = "ERROR"
                raw_results.append({
                    "scenario_id": scenario_id, "cell": sc["cell"],
                    "condition": condition, "model": model_name,
                    "prompt": prompt, "output": output, "status": status,
                })
                print(f"[{NAME}] {scenario_id} | {condition:13s} | {model_name:20s} | {status}")
                time.sleep(1)

    n_errors = sum(1 for r in raw_results if r["status"] == "ERROR")
    print(f"\n[{NAME}] {len(raw_results)} calls complete, {n_errors} errors.")
    if n_errors:
        for r in raw_results:
            if r["status"] == "ERROR":
                print(f"  ERROR: {r['scenario_id']} {r['condition']} {r['model']}: {r['output'][:150]}")

    raw_json = json.dumps(raw_results, indent=2, ensure_ascii=False)
    db.set_memory("kenji", "sprint13_phase2_raw", raw_json)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"phase2-raw-task-{task_id}",
        text=raw_json[:8000],
        metadata={"agent": "kenji", "type": "sprint13_phase2_raw", "n_errors": n_errors, "n_calls": len(raw_results)},
    )
    db.update_task(
        task_id, status="completed",
        result=f"{len(raw_results)} calls, {n_errors} errors.",
        artifact_type="pilot_data",
        artifact_payload={"memory_key": "kenji/sprint13_phase2_raw", "n_errors": n_errors},
    )

    print("\n--- stored as kenji/sprint13_phase2_raw ---")


if __name__ == "__main__":
    run()
