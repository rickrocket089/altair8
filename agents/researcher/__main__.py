"""Entry point for the Researcher agent (Kenji Ochiai).

Runs a literature-scan task end-to-end: searches arXiv for papers relevant
to the research question Sophie proposed, stores them in Postgres, then asks
Kenji to synthesize a literature brief grounded in the abstracts found.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db
from tools import papers

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

RESEARCH_QUESTION = (
    "What are the most significant documented failure modes when LLMs attempt to "
    "reason about visual layout and spatial semantics, and what approaches have "
    "shown any traction against them?"
)


def run() -> None:
    db.set_memory("kenji", "status", "online")
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Literature scan: LLM visual/spatial reasoning failure modes",
        description=RESEARCH_QUESTION,
    )

    found = papers.search_arxiv(
        "large language models visual spatial reasoning failure", max_results=5
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
                    f"Research question from Sophie:\n{RESEARCH_QUESTION}\n\n"
                    f"Papers found via arXiv search:\n\n{sources}\n\n"
                    "Synthesize a structured literature brief for the team: key "
                    "failure modes found, any approaches showing traction, and an "
                    "explicit note on where the evidence is thin. Cite papers by "
                    "their arXiv ID."
                ),
            }
        ],
    )
    brief = response.content[0].text
    db.log_usage("kenji", response.usage.input_tokens, response.usage.output_tokens)

    from tools import vectorstore

    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"brief-task-{task_id}",
        text=brief,
        metadata={"agent": "kenji", "type": "literature_brief"},
    )
    db.set_memory("kenji", "last_brief", brief)
    db.update_task(task_id, status="completed", result=brief)

    print(f"[{NAME}] Found {len(found)} papers. Brief:\n\n{brief}")


if __name__ == "__main__":
    run()
