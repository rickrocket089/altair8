"""Sprint 13, Phase 1: real piloting of BASELINE, ORDER-BEFORE, and the
knowledge-elicitation probe across all three models, on the 3 scenarios
Kenji selected (S01, S11, S18) -- before committing all 20 scenarios to
the full Phase 2 run.

Prompt construction is verbatim from Kenji's protocol Section 2.0/2.3 and
the R3 amendment -- nothing paraphrased. Audience/goal descriptor text is
verbatim from the completed controlled vocabulary (A4/A6 audience, G1/G3/G4
goal). Real API calls to claude-sonnet-4-6, gpt-5.2, gemini-flash-latest,
per the founder's model selection (2026-09-16).

This is piloting, not the confirmatory run: no reliability sub-sample, no
McNemar's test, no locked scoring yet applied to real hypothesis tests.
Purpose is to surface protocol breakage (prompt construction bugs, models
refusing the task, the elicitation probe producing unusable output, the
ORDER-BEFORE compliance check failing in practice) before the expensive
full run.
"""
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

TASK_FRAMING = "You are a communication designer preparing a presentation artifact."

# Verbatim from the completed controlled vocabulary (kenji/sprint13_phase0_protocol amendment).
AUDIENCE = {
    "A4": (
        "Your audience will act on the output of a single viewing, under time "
        "pressure, without ability to ask follow-up questions."
    ),
    "A6": (
        "Your audience receives the chart embedded in a larger document and will "
        "not read surrounding text before forming a first interpretation."
    ),
}
GOAL = {
    "G1": (
        "Your goal is to help the audience establish whether a directional "
        "change over ordered time points is monotonic, interrupted, or cyclical."
    ),
    "G3": (
        "Your goal is to help the audience understand how values are "
        "distributed across a full range, including where the bulk of "
        "observations fall and how spread out they are."
    ),
    "G4": (
        "Your goal is to support a binary or multi-option choice by making the "
        "decision-relevant difference between options perceptually immediate."
    ),
}

PILOT_SCENARIOS = {
    "S01": {
        "cell": "A4xG4",
        "audience": "A4", "goal": "G4",
        "data_description": (
            "Domain: pharmaceutical manufacturing quality control. Variables: 4 "
            "(2 categorical: production batch identifier, facility site; 2 "
            "continuous: active-ingredient concentration measured value, batch "
            "release specification threshold). Pattern: concentration values "
            "cluster near but not uniformly within the specification threshold, "
            "with a subset of batches from one facility site falling below the "
            "threshold minimum."
        ),
    },
    "S11": {
        "cell": "A6xG3",
        "audience": "A6", "goal": "G3",
        "data_description": (
            "Domain: salary distribution for a specific job family across a "
            "regional labor market. Variables: 3 (1 categorical: employment "
            "sector -- 5 sectors; 2 continuous: individual salary values for "
            "200 workers sampled per sector, years of experience per sampled "
            "worker). Pattern: salary values within each sector span a wide "
            "range; the upper tail of the distribution differs markedly across "
            "sectors; years of experience and salary values show a positive "
            "but weak association within most sectors with one sector showing "
            "negligible association."
        ),
    },
    "S18": {
        "cell": "A6xG1",
        "audience": "A6", "goal": "G1",
        "data_description": (
            "Domain: annual glacier mass balance measurements at a "
            "high-altitude monitoring site over a multi-decadal record. "
            "Variables: 2 (1 categorical: year identifier as ordered sequence "
            "-- 60 years; 1 continuous: annual net mass balance in meters of "
            "water equivalent, which can be positive or negative). Pattern: "
            "values are predominantly positive in the first 20 years, "
            "transition to a mix of positive and negative values in the "
            "middle 20 years, and are predominantly negative in the final 20 "
            "years, with the magnitude of negative values increasing in the "
            "last decade."
        ),
    },
}


def _baseline_prompt(sc: dict) -> str:
    # = ORDER-AFTER, per protocol Section 2.3 -- baseline IS the ORDER-AFTER condition.
    return (
        f"{TASK_FRAMING}\n\n"
        f"{sc['data_description']}\n\n"
        f"{AUDIENCE[sc['audience']]}\n\n"
        f"{GOAL[sc['goal']]}\n\n"
        "Please reason through this step by step. Then specify which visual "
        "form you would use."
    )


def _order_before_prompt(sc: dict) -> str:
    return (
        f"{TASK_FRAMING}\n\n"
        f"{sc['data_description']}\n\n"
        f"{AUDIENCE[sc['audience']]}\n\n"
        f"{GOAL[sc['goal']]}\n\n"
        "Before reasoning through this, commit to a visual form. Name the "
        "form in one sentence first. Then explain your reasoning."
    )


def _probe_prompt(sc: dict) -> str:
    # Verbatim from the R3 amendment. Schema only -- no audience, no goal,
    # no scenario narrative, new isolated context (not chained to the
    # BASELINE call, per R3.2's anti-anchoring requirement).
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
        model=CLAUDE_MODEL, max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    return "\n".join(b.text for b in response.content if b.type == "text")


def _call_gpt(client: OpenAI, prompt: str) -> str:
    response = client.chat.completions.create(
        model=GPT_MODEL, max_completion_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def _call_gemini(client: "genai.Client", prompt: str) -> str:
    last_error = None
    for attempt in range(6):
        try:
            response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
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

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 13, Phase 1: real pilot run (3 scenarios x 3 conditions x 3 models)",
        description="Validates the protocol before committing all 20 scenarios to Phase 2.",
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
    for scenario_id, sc in PILOT_SCENARIOS.items():
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

    # Store raw pilot data. Deliberately keeping model/condition attached here
    # (this is Kenji's working record, not what the Blind Scorer sees) --
    # a separate anonymization pass builds the blinded file for scoring.
    import json
    raw_json = json.dumps(raw_results, indent=2, ensure_ascii=False)
    db.set_memory("kenji", "sprint13_phase1_pilot_raw", raw_json)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"pilot-raw-task-{task_id}",
        text=raw_json[:8000],
        metadata={"agent": "kenji", "type": "sprint13_phase1_pilot_raw", "n_errors": n_errors},
    )
    db.update_task(
        task_id, status="completed",
        result=f"{len(raw_results)} pilot calls, {n_errors} errors.",
        artifact_type="pilot_data",
        artifact_payload={"memory_key": "kenji/sprint13_phase1_pilot_raw", "n_errors": n_errors},
    )

    print(f"\n--- stored as kenji/sprint13_phase1_pilot_raw ---")


if __name__ == "__main__":
    run()
