"""Kenji reads Gap C's two founder-supplied full texts and answers the question
candidate #11 was raised to check first: does the formal visualization-design
tradition already model AUDIENCE, or only data and task?

Both files were requested from the ACM acquisition list (2026-09-16) and
ingested into `paper_fulltext` the same day:

  - Mackinlay, "Automating the Design of Graphical Presentations of Relational
    Information" (ACM ToG, 1986). Full paper, 32 pages -- clean.
  - "Visualization Analysis and Design" -- **NOT the Munzner/CRC-Press book**.
    Inspecting the PDF after a suspiciously short extraction (5 pages / 33k
    chars from a 6.7MB file) found pdfTeX metadata from 2017 and a first line
    reading "tamaramunzner www.cs.ubc.ca/~tmm/talks.html#vad17stat545" -- this
    is a 5-slide excerpt from a talk on Munzner's own site, same title as her
    book, not the book. Founder decided 2026-09-16 not to buy the real book
    now (cost) but flagged the content as likely high-value and will try to
    acquire it across future sprints (backlog #34). Proceeding now on the
    slide excerpt with the caveat stated explicitly, per his instruction,
    rather than waiting.

Why this matters beyond Gap C itself: candidate #11 (a corpus/knowledge-graph
of existing visualizations to teach form selection) named this literature
check as the CHEAPER FIRST STEP before building anything -- if the formal
tradition already models audience, the missing dimension for hypothesis 6
narrows; if it only ever modeled data and task, that gap is real and named,
not assumed.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, fulltext, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"
MACKINLAY_SLUG = "automating-the-design-of-graphical-presentations-of-relation"
MUNZNER_SLUG = "visualization-analysis-and-design"


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    mackinlay = fulltext.read(MACKINLAY_SLUG)
    munzner_excerpt = fulltext.read(MUNZNER_SLUG)
    acquisition_list = db.get_memory("kenji", "acm_acquisition_list") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Read Gap C full texts: does the formal tradition model audience?",
        description=(
            "Founder-supplied PDFs, 2026-09-16. Mackinlay full paper; Munzner "
            "item is a 5-slide talk excerpt, not the book -- caveat applies."
        ),
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model=MODEL, max_tokens=8000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "You flagged Gap C in your own acquisition list as the one where "
            "the connectors found nothing -- Mackinlay's foundational paper "
            "and Munzner's book had to be fetched directly. The founder "
            "supplied both. Read them for real.\n\n"
            "IMPORTANT CAVEAT ON THE SECOND FILE: what you have below labeled "
            "'MUNZNER EXCERPT' is NOT Visualization Analysis and Design, the "
            "book. It is a 5-slide excerpt from a talk of the same title on "
            "Munzner's own site (confirmed via PDF metadata: pdfTeX, 2017, "
            "first line names the talk URL). The founder is not buying the "
            "book right now (cost) and will try to acquire it across future "
            "sprints. Treat every claim you make from this excerpt as "
            "provisional and scoped to five slides, explicitly -- do not "
            "write as if you have read the book, and say plainly what you "
            "cannot answer because the book isn't in hand.\n\n"
            "THE QUESTION THIS SERVES: candidate approach #11 (a corpus/"
            "knowledge-graph to teach the team's system what visual forms "
            "mean and when to use them) named this as the cheaper check to "
            "run BEFORE building anything -- does the formal, decades-old "
            "form-to-task tradition already model AUDIENCE, or only data and "
            "task? Hypothesis 6 turns on the same distinction. If it's only "
            "ever been data+task, that is what a corpus would actually need "
            "to add. If audience is already in there somewhere, say so and "
            "say exactly what 'audience' meant to that author -- reader "
            "expertise, purpose, medium, something else.\n\n"
            "ANSWER, in this order:\n\n"
            "1. MACKINLAY 1986, READ IN FULL. State the expressiveness and "
            "effectiveness criteria precisely, in his own terms. Do they take "
            "anything about the READER as input -- expertise, goal, prior "
            "knowledge -- or only the data's structure (quantitative/ordinal/"
            "nominal) and, if present, a task? Quote or closely paraphrase "
            "the passage that settles it.\n\n"
            "2. THE MUNZNER EXCERPT, READ WITH THE CAVEAT ACTIVE. What do "
            "these 5 slides actually cover (idiom structure, encoding "
            "channels, color, a line-chart idiom, link marks -- confirm or "
            "correct from what's really there)? Does anything in this "
            "excerpt reference audience or reader modeling? State clearly: "
            "'the excerpt does/does not mention X' rather than extrapolating "
            "to what the book probably says elsewhere -- you don't have the "
            "book.\n\n"
            "3. THE ANSWER TO CANDIDATE #11'S CHEAPER-FIRST QUESTION, as far "
            "as these two sources can settle it. Does the formal tradition "
            "model audience? If Mackinlay's answer is 'no, data and task "
            "only,' say that plainly -- it's a real, citable gap, not a "
            "disappointing result. If the excerpt suggests Munzner's later "
            "work (the nested model: domain/task/idiom/algorithm) might "
            "address it, name that as an open question for when the real "
            "book is available, not a finding.\n\n"
            "4. WHAT THIS MEANS FOR HYPOTHESIS 6 AND BACKLOG #23. Hypothesis "
            "6 asks whether models have internalized audience-sensitive form "
            "selection or only reproduce convention. If the formal literature "
            "itself never encoded audience, then any model trained partly on "
            "that literature's descendants (textbooks, tools, papers citing "
            "it) inherited a data+task frame by construction -- does that "
            "change how you'd interpret a positive finding on backlog #23, "
            "or not? Be precise about what does and doesn't follow.\n\n"
            "5. WHAT TO ASK FOR WHEN THE REAL BOOK ARRIVES. Given what these "
            "5 slides show, name the specific chapters/concepts worth reading "
            "first in the actual book (e.g. the nested model chapter) rather "
            "than 'read the whole thing' -- so backlog #34 has a concrete "
            "target, not just a purchase.\n\n"
            f"YOUR OWN ACQUISITION LIST, for context on how these were found:\n"
            f"{acquisition_list[:3000]}\n\n"
            f"=== FULL TEXT: MACKINLAY 1986 ===\n{mackinlay}\n\n"
            f"=== MUNZNER EXCERPT (5 SLIDES ONLY, NOT THE BOOK) ===\n{munzner_excerpt}\n"
        )}],
    ) as stream:
        resp = stream.get_final_message()

    brief = resp.content[0].text
    db.log_usage("kenji", resp.usage.input_tokens, resp.usage.output_tokens)

    db.set_memory("kenji", "gap_c_fulltext_verdict", brief)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"brief-task-{task_id}",
        text=brief,
        metadata={"agent": "kenji", "type": "gap_c_fulltext_verdict"},
    )
    db.update_task(
        task_id, status="completed", result=brief,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/gap_c_fulltext_verdict"},
    )

    print(f"[{NAME}]\n\n{brief}")
    print(f"\n\n--- {len(brief)} chars, stored as kenji/gap_c_fulltext_verdict ---")


if __name__ == "__main__":
    run()
