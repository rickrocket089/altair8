"""Sprint 7, research track: the adversarial-pairs behavioral test that
replaces Sprint 6's original (flawed) form-prediction probe.

Design logic (Ingrid's fix, Sprint 6 review): a form-prediction probe can't
distinguish principled reasoning from confabulation, because confabulated
reasoning can be specific and internally consistent enough to predict the
form from anyway. The stronger test is adversarial pairs: hold content
constant, and construct two audience/goal conditions per content --
(1) a NORMAL condition where the textbook-canonical visual form for that
content type is also the right answer, and (2) an ADVERSARIAL condition
where the canonical form is still the naive/expected answer, but the
audience and goal clearly call for a different form entirely (not just a
different chart sub-type -- a categorical medium switch, matching what
Sprint 6 found was the strongest evidence of tracking, e.g. Claude's A2
prose response).

If a model keeps recommending the canonical form in the adversarial
condition, or recommends the right non-canonical form but without reasoning
that explicitly names audience/goal as overriding content-type convention,
that's evidence against principled reasoning. If it switches AND its
reasoning explicitly makes the override argument, that's real evidence the
reasoning is doing causal work -- not just retroactively describing a
form chosen some other way.

CONSTRUCTION VALIDITY (Ingrid's Sprint 6 flag: who validates the
adversarial condition is actually met?): every pair below documents (a) the
canonical mapping as a standard, uncontroversial data-viz convention -- not
this team's opinion -- and (b) the specific audience/goal mechanism that
overrides it. Ingrid's Sprint 7 review should assess this construction,
not just the model outputs.
"""
import os
import time

from dotenv import load_dotenv
from anthropic import Anthropic
from openai import OpenAI
from google import genai
from google.genai import errors as genai_errors

from agents.permissions import require_tool
from agents.researcher_visual.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

CLAUDE_MODEL = "claude-sonnet-4-6"
GPT_MODEL = "gpt-5.2"
GEMINI_MODEL = "gemini-flash-latest"

ADVERSARIAL_PAIRS = [
    {
        "pair_id": "AP1",
        "canonical_form": "line chart",
        "canonical_rationale": "Standard data-viz convention: a numeric value tracked over time is a time-series trend -- textbook default is a line chart.",
        "content": "Website traffic (unique visitors) over the last 12 months, generally increasing with a dip in month 8.",
        "override_mechanism": "Audience needs a 3-second glance-and-act alert, not a trend to study -- the goal is immediate action, not comprehension of trajectory.",
        "variants": [
            {
                "label": "AP1-normal",
                "audience": "Internal quarterly business review, mixed roles.",
                "goal": "Show the traffic trend over the year.",
                "expect_canonical": True,
            },
            {
                "label": "AP1-adversarial",
                "audience": "Frontline warehouse staff, glancing at a shared TV screen for 3 seconds, no data background.",
                "goal": "Communicate that today's traffic is critically below target and immediate action is needed right now.",
                "expect_canonical": False,
            },
        ],
    },
    {
        "pair_id": "AP2",
        "canonical_form": "bar chart",
        "canonical_rationale": "Standard data-viz convention: comparing a metric across discrete categories (here, people) is a categorical comparison -- textbook default is a bar chart.",
        "content": "Support ticket resolution time for 6 support agents this month.",
        "override_mechanism": "Audience is one specific underperforming individual in a private coaching conversation -- ranking them against named peers undermines the goal of supportive, non-comparative feedback.",
        "variants": [
            {
                "label": "AP2-normal",
                "audience": "Support team lead, weekly performance review.",
                "goal": "Compare resolution times across agents to spot outliers.",
                "expect_canonical": True,
            },
            {
                "label": "AP2-adversarial",
                "audience": "One specific underperforming agent, in a private 1:1 coaching conversation.",
                "goal": "Give constructive, supportive feedback without making the agent feel publicly ranked or compared against named peers.",
                "expect_canonical": False,
            },
        ],
    },
    {
        "pair_id": "AP3",
        "canonical_form": "pie chart",
        "canonical_rationale": "Standard data-viz convention: showing how a whole divides into parts is a part-to-whole relationship -- textbook default is a pie chart (or 100% stacked bar).",
        "content": "Marketing budget allocation across 5 channels this quarter.",
        "override_mechanism": "Audience needs exact, verifiable dollar figures to reconcile against invoices -- a pie chart communicates proportion, not precision, and actively works against the goal.",
        "variants": [
            {
                "label": "AP3-normal",
                "audience": "Marketing team all-hands.",
                "goal": "Show how the budget is proportionally split across channels.",
                "expect_canonical": True,
            },
            {
                "label": "AP3-adversarial",
                "audience": "Finance controller doing a budget audit.",
                "goal": "Provide precise, verifiable numbers that can be reconciled against invoices, not a visual impression of proportion.",
                "expect_canonical": False,
            },
        ],
    },
    {
        "pair_id": "AP4",
        "canonical_form": "flowchart / process diagram",
        "canonical_rationale": "Standard data-viz convention: a multi-step sequential process is causal/sequential content -- textbook default is a flowchart.",
        "content": "The 6-step approval process for a new vendor contract.",
        "override_mechanism": "Audience needs the answer to one specific question fast, not to learn the process -- a flowchart invites study, which works against a goal that requires an instant answer.",
        "variants": [
            {
                "label": "AP4-normal",
                "audience": "New employees during onboarding.",
                "goal": "Teach the complete workflow so they understand how contracts get approved.",
                "expect_canonical": True,
            },
            {
                "label": "AP4-adversarial",
                "audience": "A busy VP who needs one specific answer: what step is currently blocking a specific deal.",
                "goal": "Answer one specific question in the time it takes to read a sentence, not teach the process.",
                "expect_canonical": False,
            },
        ],
    },
    {
        "pair_id": "AP5",
        "canonical_form": "map",
        "canonical_rationale": "Standard data-viz convention: data indexed by geographic region is spatial content -- textbook default is a map.",
        "content": "Regional sales performance across 8 countries.",
        "override_mechanism": "Audience is reading a plain-text async message on a phone and skimming for seconds -- an embedded/interactive map doesn't render or scan well in that medium, and the goal only needs the outliers named, not spatial context.",
        "variants": [
            {
                "label": "AP5-normal",
                "audience": "Global sales all-hands presentation.",
                "goal": "Show the geographic distribution of performance across regions.",
                "expect_canonical": True,
            },
            {
                "label": "AP5-adversarial",
                "audience": "A recipient reading a plain-text async chat digest on a phone, skimming for 5 seconds.",
                "goal": "Quickly convey which 2 regions need attention, nothing else.",
                "expect_canonical": False,
            },
        ],
    },
    {
        "pair_id": "AP6",
        "canonical_form": "scatter plot",
        "canonical_rationale": "Standard data-viz convention: the relationship between two continuous variables is a correlation -- textbook default is a scatter plot.",
        "content": "Relationship between customer onboarding time and 90-day retention, across 200 customers.",
        "override_mechanism": "Audience is a non-technical external reader of marketing content -- a scatter plot reads as cold/analytical, and the goal is persuasion through story, not demonstrating a statistical relationship.",
        "variants": [
            {
                "label": "AP6-normal",
                "audience": "Internal product analytics team.",
                "goal": "Show the correlation pattern between onboarding time and 90-day retention.",
                "expect_canonical": True,
            },
            {
                "label": "AP6-adversarial",
                "audience": "External blog post for prospective customers, non-technical.",
                "goal": "Persuade the reader that fast onboarding matters, using a compelling story, not a statistical demonstration.",
                "expect_canonical": False,
            },
        ],
    },
]

PROMPT_TEMPLATE = """You are producing a business communication. Given the following content, audience, and communication goal, decide what VISUAL FORM you would use to present it (e.g. a specific chart type, a table, a diagram, plain prose, a single statistic, something else) and explain WHY that form serves this specific audience and goal better than the alternatives you considered.

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
        model=CLAUDE_MODEL, max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return "\n".join(block.text for block in response.content if block.type == "text")


def _call_gpt(client: OpenAI, content: str, audience: str, goal: str) -> str:
    prompt = PROMPT_TEMPLATE.format(content=content, audience=audience, goal=goal)
    response = client.chat.completions.create(
        model=GPT_MODEL, max_completion_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


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
            if e.code != 429:
                raise
            last_error = e
            time.sleep(25 * (attempt + 1))
    raise last_error


def run() -> None:
    require_tool("naledi", "write_cognitive_annotation")
    db.set_memory("naledi", "status", "online")
    sprint_id = db.get_sprint_id(7)
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="naledi",
        title="Sprint 7: adversarial-pairs behavioral test (3 models)",
        description="Replaces Sprint 6's flawed form-prediction probe. 6 pairs, 12 variants, Claude/GPT/Gemini.",
    )

    claude_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    gpt_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    raw_results = []
    for pair in ADVERSARIAL_PAIRS:
        for variant in pair["variants"]:
            audience = variant["audience"]
            goal = variant["goal"]
            content = pair["content"]

            claude_answer = _call_claude(claude_client, content, audience, goal)
            gpt_answer = _call_gpt(gpt_client, content, audience, goal)
            gemini_answer = _call_gemini(gemini_client, content, audience, goal)
            time.sleep(13)  # stay under Gemini free-tier ~5 req/min

            raw_results.append(
                {
                    "pair_id": pair["pair_id"],
                    "canonical_form": pair["canonical_form"],
                    "canonical_rationale": pair["canonical_rationale"],
                    "override_mechanism": pair["override_mechanism"],
                    "label": variant["label"],
                    "content": content,
                    "audience": audience,
                    "goal": goal,
                    "expect_canonical": variant["expect_canonical"],
                    "claude_answer": claude_answer,
                    "gpt_answer": gpt_answer,
                    "gemini_answer": gemini_answer,
                }
            )
            print(f"[{NAME}] Collected {variant['label']}")

    raw_data_text = ""
    for pair in ADVERSARIAL_PAIRS:
        raw_data_text += (
            f"\n\n{'='*70}\nPAIR {pair['pair_id']} -- canonical form: {pair['canonical_form']}\n"
            f"Canonical rationale: {pair['canonical_rationale']}\n"
            f"Override mechanism (why the adversarial variant should NOT get the canonical form): {pair['override_mechanism']}\n"
        )
        for r in [x for x in raw_results if x["pair_id"] == pair["pair_id"]]:
            raw_data_text += (
                f"\n--- {r['label']} (expects canonical form: {r['expect_canonical']}) ---\n"
                f"CONTENT: {r['content']}\nAUDIENCE: {r['audience']}\nGOAL: {r['goal']}\n\n"
                f"Claude:\n{r['claude_answer']}\n\n"
                f"GPT:\n{r['gpt_answer']}\n\n"
                f"Gemini:\n{r['gemini_answer']}\n"
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
                    "Sprint 7 research track: the adversarial-pairs test that "
                    "replaces Sprint 6's flawed form-prediction probe (Ingrid's "
                    "fix). 6 pairs, 12 variants, 3 models (Claude, GPT, "
                    "Gemini) -- same prompt format as Sprint 6 for continuity.\n\n"
                    "METHOD: each pair holds content constant. The 'normal' "
                    "variant's audience/goal matches the textbook-canonical "
                    "form for that content type -- this is a sanity check, "
                    "not a good test on its own. The 'adversarial' variant's "
                    "audience/goal is constructed so the canonical form is "
                    "actively wrong -- a categorical medium switch is called "
                    "for, not just a different chart sub-type (per Sprint 6's "
                    "finding that categorical switches, like Claude choosing "
                    "prose over any chart, were the clearest evidence of "
                    "tracking).\n\n"
                    "For EACH pair, for EACH model, score explicitly:\n"
                    "1. Did it recommend the canonical form or a different "
                    "one in the adversarial variant?\n"
                    "2. If different: does the REASONING explicitly name the "
                    "audience/goal as the reason for overriding the obvious/"
                    "conventional choice for this content type -- or does it "
                    "just describe the chosen form's properties without "
                    "engaging why convention was overridden?\n"
                    "3. Only a 'yes' on both 1 and 2 counts as evidence of "
                    "principled reasoning actually doing causal work. A model "
                    "that picks the right non-canonical form but reasons about "
                    "it generically (not naming the override) is a weaker "
                    "case -- flag this distinction, don't collapse it.\n\n"
                    "Structure your analysis as:\n"
                    "WHAT THE EVIDENCE SHOWS: go pair by pair, model by "
                    "model. Quote specific evidence for the scoring above.\n\n"
                    "WHAT THIS MIGHT IMPLY: your interpretation, clearly "
                    "flagged as interpretation. How does this compare to "
                    "Sprint 6's findings (medium-frame anchoring for GPT, the "
                    "candidate form-conservatism pattern for Gemini, no clear "
                    "failure mode for Claude) -- do those patterns replicate "
                    "under adversarial pressure, or was Sprint 6's picture "
                    "specific to those 6 variants? Be honest about sample "
                    "size: 6 pairs, 12 variants, one run per model -- bigger "
                    "than Sprint 6 but still a pilot, not a robust study "
                    "(Naledi's own Sprint 6 brief called for 15-20 pairs).\n\n"
                    "End with a direct answer: does this adversarial design "
                    "actually distinguish principled reasoning from "
                    "confabulation better than Sprint 6's original approach "
                    "did? And: overall, is the evidence across Sprint 6 + "
                    "Sprint 7 now sufficient to inform (not decide) the "
                    "founder's Direction A vs Direction B choice, or does it "
                    "remain purely directional?\n\n"
                    f"RAW DATA (real API calls, not simulated):\n{raw_data_text}\n\n"
                    "Also include a full appendix of raw responses at the end, "
                    "organized by pair and variant, all 12 variants x 3 "
                    "models, in full -- do not truncate or summarize any "
                    "response."
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    analysis = response.content[0].text
    db.log_usage("naledi", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"adversarial-pairs-test-task-{task_id}",
        text=analysis,
        metadata={"agent": "naledi", "type": "adversarial_pairs_test"},
    )
    db.set_memory("naledi", "adversarial_pairs_test", analysis)
    db.update_task(
        task_id, status="completed", result=analysis,
        artifact_type="research_brief",
        artifact_payload={"memory_key": "naledi/adversarial_pairs_test"},
    )

    print(f"[{NAME}] Adversarial-pairs test complete.\n\n{analysis}")


if __name__ == "__main__":
    run()
