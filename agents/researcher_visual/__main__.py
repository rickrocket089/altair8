"""Entry point for the Researcher agent (Dr. Naledi Mokoena).

Builds on Kenji's literature brief with a cognitive-science / visual-encoding
angle: searches arXiv for complementary work, then synthesizes concrete
implications for the Developer.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.researcher_visual.persona import NAME, SYSTEM_PROMPT
from tools import db, papers, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))


def run() -> None:
    db.set_memory("naledi", "status", "online")
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="naledi",
        title="Cognitive-science review: visual encoding & layout comprehension",
        description="Build on Kenji's literature brief from a cognitive-science/HCI angle.",
    )

    kenji_brief = db.get_memory("kenji", "last_brief") or "(no prior brief found)"

    found = papers.search_arxiv(
        "information visualization cognitive load visual encoding comprehension",
        max_results=5,
    )
    for paper in found:
        papers.save_paper(paper)

    sources = "\n\n".join(
        f"[{p['arxiv_id']}] {p['title']}\nAuthors: {p['authors']}\nAbstract: {p['abstract']}"
        for p in found
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Kenji's literature brief on LLM visual/spatial reasoning failure "
                    f"modes:\n\n{kenji_brief}\n\n"
                    f"Additional papers found on visual encoding / cognitive load:\n\n{sources}\n\n"
                    "Write a companion brief from your cognitive-science/HCI angle: what "
                    "do we know about why some visual encodings reduce cognitive load and "
                    "others increase it? End with a concrete, numbered list of implications "
                    "for Mateo (the Developer) building a visualization engine — be specific "
                    "about what to build differently from a static slide."
                ),
            }
        ],
    )
    brief = response.content[0].text
    db.log_usage("naledi", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"brief-task-{task_id}",
        text=brief,
        metadata={"agent": "naledi", "type": "cognitive_science_brief"},
    )
    db.set_memory("naledi", "last_brief", brief)
    db.update_task(task_id, status="completed", result=brief)

    print(f"[{NAME}] Found {len(found)} papers. Brief:\n\n{brief}")


if __name__ == "__main__":
    run()
