"""Entry point for Naledi's Sprint 6: controlled behavioral testing of
whether base foundation models show principled reasoning about visual-form
selection, or post-hoc confabulation. Answers Ingrid's open question from
Sprint 4's review.

SCOPE DECLARATION (per Sophie's new pre-sprint requirement):
Covered: Claude (Sonnet 4.6, via ANTHROPIC_API_KEY) and GPT (via the existing
OPENAI_API_KEY, previously scoped to image generation only -- expanded here
to a text/reasoning call, no new credential needed).
Excluded: Gemini -- no Google API key exists in this project. Flagged as a
follow-up, not silently dropped.

Method: paired scenarios that hold content constant while varying either the
audience or the communication goal. If a model's visual-form choice and
reasoning shift appropriately between paired variants, that's evidence of
principled reasoning. If the choice/reasoning stays templated regardless of
what changed, that's evidence of confabulation -- a plausible-sounding
justification generated after the form was already the default answer.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic
from openai import OpenAI

from agents.permissions import require_tool
from agents.researcher_visual.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

CLAUDE_MODEL = "claude-sonnet-4-6"
GPT_MODEL = "gpt-5.2"

# Each pair shares the same underlying content but varies ONE variable
# (audience or goal) -- the test is whether the model's form choice and
# reasoning track that variable or stay fixed.
SCENARIO_PAIRS = [
    {
        "pair_id": "A",
        "varies": "audience",
        "shared_content": "Quarterly revenue data: down 15% in Q3, driven by supply chain delays in the APAC region.",
        "variants": [
            {
                "label": "A1 -- board of directors",
                "audience": "The board of directors, who need to decide within this meeting whether to approve emergency supply-chain budget.",
                "goal": "Get a fast, confident go/no-go decision on emergency spending.",
            },
            {
                "label": "A2 -- new customer support reps",
                "audience": "Newly hired customer support reps in their first week, who need to understand why customers have been complaining about delays.",
                "goal": "Build basic situational understanding, not drive a decision.",
            },
        ],
    },
    {
        "pair_id": "B",
        "varies": "goal",
        "shared_content": "Employee satisfaction survey scores across 5 departments, tracked over 2 years.",
        "variants": [
            {
                "label": "B1 -- identify urgent problem",
                "audience": "Senior leadership team, biweekly ops review.",
                "goal": "Identify which single department needs urgent intervention.",
            },
            {
                "label": "B2 -- celebrate improvement",
                "audience": "All-hands company meeting, all employees.",
                "goal": "Celebrate overall company-wide culture improvement.",
            },
        ],
    },
    {
        "pair_id": "C",
        "varies": "content type (control -- same audience/goal, different content shape)",
        "shared_content": None,  # each variant has distinct content, by design
        "variants": [
            {
                "label": "C1 -- numeric trend",
                "content": "Monthly active users over the last 18 months, steadily climbing.",
                "audience": "General internal company update, mixed roles.",
                "goal": "Show healthy growth momentum.",
            },
            {
                "label": "C2 -- causal process",
                "content": "The five sequential steps in the company's supply chain, from raw material sourcing to delivery, and where delays currently occur.",
                "audience": "General internal company update, mixed roles.",
                "goal": "Explain a causal process, not show a trend.",
            },
        ],
    },
]

PROMPT_TEMPLATE = """You are producing a business communication. Given the following content, audience, and communication goal, decide what VISUAL FORM you would use to present it (e.g. a specific chart type, a table, a diagram, plain prose, a timeline, something else) and explain WHY that form serves this specific audience and goal better than the alternatives you considered.

CONTENT: {content}
AUDIENCE: {audience}
GOAL: {goal}

Answer in this exact format:
FORM: <the visual form you chose, one line>
REASONING: <2-4 sentences explaining why this form serves this specific audience and goal>
"""


def _call_claude(client: Anthropic, content: str, audience: str, goal: str) -> str:
    prompt = PROMPT_TEMPLATE.format(content=content, audience=audience, goal=goal)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return "\n".join(block.text for block in response.content if block.type == "text")


def _call_gpt(client: OpenAI, content: str, audience: str, goal: str) -> str:
    prompt = PROMPT_TEMPLATE.format(content=content, audience=audience, goal=goal)
    response = client.chat.completions.create(
        model=GPT_MODEL,
        max_completion_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def run() -> None:
    require_tool("naledi", "write_cognitive_annotation")
    db.set_memory("naledi", "status", "online")
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="naledi",
        title="Sprint 6: behavioral testing of principled vs. confabulated visual-form reasoning",
        description="Controlled paired-scenario test across Claude and GPT.",
    )

    claude_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    gpt_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    raw_results = []
    for pair in SCENARIO_PAIRS:
        for variant in pair["variants"]:
            content = variant.get("content", pair.get("shared_content"))
            audience = variant["audience"]
            goal = variant["goal"]

            claude_answer = _call_claude(claude_client, content, audience, goal)
            gpt_answer = _call_gpt(gpt_client, content, audience, goal)

            raw_results.append(
                {
                    "pair_id": pair["pair_id"],
                    "varies": pair["varies"],
                    "label": variant["label"],
                    "content": content,
                    "audience": audience,
                    "goal": goal,
                    "claude_answer": claude_answer,
                    "gpt_answer": gpt_answer,
                }
            )

    raw_data_text = ""
    for r in raw_results:
        raw_data_text += (
            f"\n=== Pair {r['pair_id']} ({r['varies']}) — {r['label']} ===\n"
            f"CONTENT: {r['content']}\nAUDIENCE: {r['audience']}\nGOAL: {r['goal']}\n\n"
            f"--- Claude Sonnet 4.6 response ---\n{r['claude_answer']}\n\n"
            f"--- GPT response ---\n{r['gpt_answer']}\n"
        )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Sprint 6 question: do base foundation models show "
                    "principled reasoning about visual-form selection, or "
                    "post-hoc confabulation? This answers Ingrid's open "
                    "question from Sprint 4.\n\n"
                    "SCOPE DECLARATION: Claude and GPT tested (both existing "
                    "API keys, no new credentials). Gemini excluded -- no "
                    "Google API key exists in this project; flag this as a "
                    "follow-up, don't let it pass silently.\n\n"
                    "METHOD: 3 paired scenarios, each pair holding content "
                    "constant while varying audience (pair A), goal (pair "
                    "B), or as a control, varying content type while holding "
                    "audience/goal constant (pair C, to confirm the models "
                    "respond to genuine differences at all, not just noise). "
                    "For each variant, both models were asked to choose a "
                    "visual form and justify it.\n\n"
                    f"RAW DATA (real API calls, not simulated):\n{raw_data_text}\n\n"
                    "Structure your analysis as:\n"
                    "WHAT THE EVIDENCE SHOWS: for each pair, does the "
                    "model's form choice AND reasoning actually shift "
                    "between the two variants in a way that tracks the "
                    "changed variable? Or does it stay the same/generic "
                    "regardless? Do this separately for Claude and for GPT -- "
                    "they may behave differently. Quote specific evidence, "
                    "don't just assert a verdict.\n\n"
                    "WHAT THIS MIGHT IMPLY: your interpretation, clearly "
                    "flagged as interpretation -- what would this pattern "
                    "mean for direction (a) of Altair8's solution space (an "
                    "additional-reasoning-layer approach)? Be honest about "
                    "the small sample size (3 pairs, 6 variants) -- this is "
                    "a pilot test, not a definitive behavioral study. Note "
                    "explicitly what a larger follow-up would need "
                    "(more pairs, more models including Gemini, blind "
                    "scoring by a separate rater) to make the finding "
                    "robust.\n\n"
                    "End with a direct answer to Ingrid's Sprint 4 question: "
                    "is the reasoning principled or confabulated, and how "
                    "confident are you in that answer given the sample size?"
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    analysis = response.content[0].text
    db.log_usage("naledi", response.usage.input_tokens, response.usage.output_tokens)

    full_brief = f"{analysis}\n\n---\n\n## Appendix: Raw Model Responses\n{raw_data_text}"

    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"behavioral-reasoning-test-task-{task_id}",
        text=full_brief,
        metadata={"agent": "naledi", "type": "behavioral_reasoning_test"},
    )
    db.set_memory("naledi", "behavioral_reasoning_test", full_brief)
    db.update_task(
        task_id, status="completed", result=full_brief,
        artifact_type="research_brief", artifact_payload={"memory_key": "naledi/behavioral_reasoning_test"},
    )

    print(f"[{NAME}] Behavioral reasoning test complete.\n\n{full_brief}")


if __name__ == "__main__":
    run()
