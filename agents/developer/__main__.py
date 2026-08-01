"""Entry point for the Developer agent (Mateo Fittipaldi).

Reads the Researchers' briefs from Postgres, asks Mateo to design one concrete
visualization prototype informed by their findings, and writes the resulting
self-contained HTML file to workspace/outputs/.
"""
import os
import re

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.developer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "workspace", "outputs", "prototype.html"
)


def run() -> None:
    db.set_memory("mateo", "status", "online")
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="mateo",
        title="Prototype: semantic visualization primitive",
        description="Build one concrete HTML prototype informed by Kenji's and Naledi's briefs.",
    )

    kenji_brief = db.get_memory("kenji", "last_brief") or "(no prior brief found)"
    naledi_brief = db.get_memory("naledi", "last_brief") or "(no prior brief found)"

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Kenji's literature brief:\n\n{kenji_brief}\n\n"
                    f"Naledi's cognitive-science brief:\n\n{naledi_brief}\n\n"
                    "Design and build ONE concrete, self-contained HTML prototype "
                    "(inline CSS/JS, no external dependencies) that demonstrates a "
                    "visualization approach directly motivated by their findings — "
                    "something that could not just be a PPT slide. Keep it focused: "
                    "one clear idea, not an exhaustive claims graph. "
                    "First write 2-4 sentences explaining what you built and which "
                    "specific finding motivated it. Then output the complete HTML "
                    "in a single ```html fenced code block, and make sure the block "
                    "is closed with a trailing ``` ."
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    text = response.content[0].text
    db.log_usage("mateo", response.usage.input_tokens, response.usage.output_tokens)

    match = re.search(r"```html\n(.*?)```", text, re.DOTALL)
    if match:
        html = match.group(1).strip()
        explanation = text[: match.start()].strip()
    else:
        open_fence = re.search(r"```html\n", text)
        if open_fence:
            html = text[open_fence.end():].strip()
            explanation = text[: open_fence.start()].strip()
        else:
            html = ""
            explanation = text

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    vectorstore.remember(
        collection_name="developer_memory",
        doc_id=f"prototype-task-{task_id}",
        text=explanation,
        metadata={"agent": "mateo", "type": "prototype_explanation"},
    )
    db.set_memory("mateo", "last_explanation", explanation)
    db.update_task(task_id, status="completed", result=explanation)

    print(f"[{NAME}] Wrote prototype to {OUTPUT_PATH}\n\n{explanation}")


if __name__ == "__main__":
    run()
