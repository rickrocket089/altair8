"""Entry point for Mateo's Sprint 4 engineering question: how do foundation-
model providers technically implement skill/capability selection and
loading -- separate from Kenji's content question (does it already solve
our research problem). Pure orchestration/mechanism analysis, same spirit
as his Sprint 3 AI-Scientist-v2 review.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.developer.persona import NAME, SYSTEM_PROMPT
from agents.permissions import require_tool
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

SPRINT_QUESTION = (
    "How do foundation-model providers (Anthropic, OpenAI, Google, Microsoft) "
    "technically implement skill/capability selection and loading -- and "
    "which of those mechanisms are worth Altair8 borrowing?"
)

MODEL = "claude-sonnet-4-6"
TOOLS = [{"type": "web_search_20260209", "name": "web_search"}]

ANTHROPIC_MECHANISM_GROUND_TRUTH = '''
=== DIRECTLY OBSERVED: how Claude's own Skill system works (from the orchestrating session's own tool definitions and skill invocations) ===

- Skills are advertised to the model via a listing of name + one-line description (a "system-reminder" style list), not loaded in full up front. The model decides which skill applies by matching the current task to those descriptions, then explicitly invokes the skill by name through a dedicated tool call. This is description-based routing + explicit invocation, not automatic silent injection.
- Some skills carry hard trigger conditions written directly into their description (e.g. one skill's listing text says, verbatim style: "read it BEFORE opening the target file... whenever: the prompt names Claude/Anthropic... OR the task is LLM-shaped with provider unstated" and gives an explicit SKIP condition too) -- i.e. the routing logic (when to fire, when NOT to fire) is authored as part of the skill's own metadata, not hardcoded in the host application.
- Skills have a base directory on disk (observed literally: "Base directory for this skill: .../dataviz") containing a main instructions file plus a `references/` subfolder (topic-split markdown files loaded selectively, only when that sub-topic is actually needed) and a `scripts/` subfolder (runnable code, e.g. a palette validator script) -- i.e. the skill is not just a prompt, it can ship executable verification tools alongside the instructions, and the model is told to run them rather than "reason" about the equivalent check.
- A related but distinct mechanism exists for tools (not skills): large tool registries are kept "deferred" -- only name-visible until a search-style lookup call fetches the full parameter schema for the specific tools needed for the current task, rather than loading every possible tool's full schema into context permanently. This is a lazy-loading pattern for capabilities, separate from the skill-routing mechanism above but solving a similar "don't front-load everything" problem.
- Skills can specify that they run "in a subagent and return the finished result" as an alternative to loading instructions into the current turn -- i.e. there are two integration modes: inline instruction-injection vs. delegated sub-execution.
'''


def _extract_text(content) -> str:
    return "\n".join(block.text for block in content if block.type == "text")


def run() -> None:
    require_tool("mateo", "write_task_artifact")
    db.set_memory("mateo", "status", "online")
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="mateo",
        title="Sprint 4: skill/capability mechanism review",
        description=SPRINT_QUESTION,
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    user_message = {
        "role": "user",
        "content": (
            f"Sprint question: {SPRINT_QUESTION}\n\n"
            "This is pure engineering/orchestration analysis -- like your "
            "Sprint 3 AI-Scientist-v2 pattern review, not a content/research "
            "question. Kenji is separately covering whether these "
            "capabilities solve Altair8's actual research problem; ignore "
            "that angle entirely here.\n\n"
            "TIER 1 -- DIRECTLY OBSERVED (ground truth, cite precisely, this "
            "is more reliable than anything you'll find by web search):\n\n"
            f"{ANTHROPIC_MECHANISM_GROUND_TRUTH}\n\n"
            "TIER 2 -- WEB SEARCH REQUIRED for OpenAI, Google, and Microsoft: "
            "investigate how each technically routes a user request to the "
            "right capability. For OpenAI: how GPTs/Actions/tool-calling "
            "decide which function or GPT to invoke, how Custom GPT "
            "instructions are loaded, any public documentation on their "
            "routing/selection logic. For Google: Gemini's extensions/Gems "
            "mechanism, how 'Apps'/tool integrations are selected at runtime. "
            "For Microsoft: how Copilot plugins/Graph connectors are "
            "discovered and invoked. Be explicit about what's documented vs. "
            "inferred from behavior.\n\n"
            "For each mechanism found (Anthropic's included), evaluate against "
            "the same criteria Ingrid will apply: is the routing (a) "
            "description-based matching, (b) explicit rule-based triggers, "
            "(c) something else? Is capability content loaded eagerly or "
            "lazily? Is there a verification/validation step built into the "
            "capability itself (like the dataviz palette validator script), "
            "or is it prompt-only guidance with no executable check?\n\n"
            "Then produce a pattern table like your Sprint 3 one: pattern | "
            "source | verdict (adopt as-is / adopt adapted / skip) | concrete "
            "change for Altair8's own `agents/permissions.py` and sprint "
            "pipeline. Pay specific attention to whether the 'lazy-loading "
            "deferred capability' pattern and the 'ship an executable "
            "validator alongside the instructions' pattern (both directly "
            "observed in Tier 1) are worth adopting -- these are new since "
            "Sprint 3's AI-Scientist-v2 review and weren't covered there.\n\n"
            "End with a priority order for what to ship first, same style as "
            "your Sprint 3 recommendation."
        ),
    }
    messages = [user_message]

    response = client.messages.create(
        model=MODEL, max_tokens=8000, system=SYSTEM_PROMPT, tools=TOOLS, messages=messages
    )
    total_input = response.usage.input_tokens
    total_output = response.usage.output_tokens

    while response.stop_reason == "pause_turn":
        messages = [user_message, {"role": "assistant", "content": response.content}]
        response = client.messages.create(
            model=MODEL, max_tokens=8000, system=SYSTEM_PROMPT, tools=TOOLS, messages=messages
        )
        total_input += response.usage.input_tokens
        total_output += response.usage.output_tokens

    report = _extract_text(response.content)
    db.log_usage("mateo", total_input, total_output)

    vectorstore.remember(
        collection_name="developer_memory",
        doc_id=f"skill-mechanism-review-task-{task_id}",
        text=report,
        metadata={"agent": "mateo", "type": "skill_mechanism_review"},
    )
    db.set_memory("mateo", "skill_mechanism_review", report)
    db.update_task(
        task_id, status="completed", result=report,
        artifact_type="pattern_review",
        artifact_payload={"memory_key": "mateo/skill_mechanism_review"},
    )

    print(f"[{NAME}] Skill mechanism review complete.\n\n{report}")


if __name__ == "__main__":
    run()
