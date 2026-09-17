"""Kenji distills the core principles of Barbara Minto's Pyramid
Principle and Gene Zelazny's "Say It With Charts" in his own words --
NOT verbatim reproduction of copyrighted text. Real gap caught 2026-09-17:
neither had ever been referenced or ingested anywhere in this project,
despite Zelazny's chart-choice framework being close prior art for
Mechanism A's core question, and Minto's pyramid structure directly
grounding the "Annotated Pyramid" seed contract that was specified
without knowing its actual source.

Licensing note (per the founder's explicit path-3 decision): both books
are commercially published and not open-access. Full-text copies found
online during sourcing were predominantly on file-sharing sites of
dubious legality (Scribd, PDFRoom, dokumen.pub) -- not used. Input to
this script is real, freely-accessible SECONDARY material only (multiple
independent summary/explainer sources, gathered via live web search),
consistent with Candidate #11's own on-record licensing caution. Kenji
synthesizes and cites these sources; he does not receive or reproduce
book text.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore
from tools.llm_call import stream_complete

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"

SOURCE_MATERIAL = """REAL SECONDARY MATERIAL, gathered via live web search 2026-09-17
(freely-accessible summary/explainer sources, NOT the copyrighted book texts).
Multiple independent sources corroborate each point below.

=== BARBARA MINTO -- THE PYRAMID PRINCIPLE ===
Sources: thinkinsights.net/strategy/scqa-logic; modelthinkers.com/mental-model/minto-pyramid-scqa;
en.wikipedia.org/wiki/MECE_principle; think-cell.com (Pyramid Principle for PowerPoint);
managementconsulted.com/pyramid-principle/; strategyu.co (Structure Your Ideas: Pyramid Principle)

- Developed by Barbara Minto (first female post-MBA hire at McKinsey), 1970s. "The Pyramid
  Principle: Logic in Writing and Thinking."
- CORE STRUCTURE: top-down, answer-first. One main idea (Assertion) at the top, supporting
  Arguments below it, each backed by Data. This inverts traditional build-to-conclusion writing.
- SCQA FRAMEWORK (situation-setting device): Situation (context the audience can easily agree
  with) -> Complication (what is changing/going wrong, why action/analysis is needed) ->
  Question (the core issue this raises) -> Answer (the recommendation/solution). SCQA is how
  a pyramid-structured argument is introduced before the top-down assertion is stated.
- MECE PRINCIPLE (Mutually Exclusive, Collectively Exhaustive): the grouping discipline that
  makes a pyramid logically sound -- any set of supporting ideas grouped under a single point
  must not overlap (mutually exclusive) and must together cover the relevant space (collectively
  exhaustive). This is the test for whether a grouping is well-formed, not just plausible-looking.
- VERTICAL LOGIC: every level of the pyramid must be a genuine summary of the level below it --
  derived from it, not just thematically related to it. You cannot derive a summary idea from a
  grouping unless the grouped ideas are logically the same kind of thing and logically ordered.
- HORIZONTAL LOGIC (grouping/ordering): ideas within one grouping must be the same kind of idea
  at the same level of abstraction, and must be logically ordered. Minto names four valid ordering
  principles: deductive (argument premises), chronological (sequence in time), structural
  (e.g. by location/business unit), comparative (ranked by some measure).

=== GENE ZELAZNY -- SAY IT WITH CHARTS ===
Sources: cliffsnotes.com/study-notes/28110394; blinkist.com/en/books/say-it-with-charts-en;
antoinebuteau.com/lessons-from-gene-zelazny/; bethkanter.org/chart-formats/;
oreilly.com/library/view/say-it-with/9780071369978/

- Gene Zelazny was Director of Visual Communications at McKinsey & Company for over 40 years.
  "Say It With Charts: The Executive's Guide to Visual Communication."
- CORE PRINCIPLE: chart form selection must be driven by the MESSAGE (the specific point being
  made), not by the data itself or by aesthetic preference. "It is your message ... what you
  want to show, the specific point you want to make" that determines the right form -- the same
  dataset can support different chart choices depending on what point is being asserted.
- THE FIVE RELATIONSHIP TYPES, each with one primary chart form:
  1. COMPONENT (parts of a whole) -> Pie Chart
  2. ITEM (ranking discrete items against each other) -> Bar Chart
  3. TIME SERIES (change over time) -> Line Chart
  4. FREQUENCY DISTRIBUTION (spread of items across a range) -> Histogram / Column Chart
  5. CORRELATION (relationship between two variables) -> Scatter Plot (or paired bar chart)
- The mapping is explicitly a MESSAGE-TO-FORM mapping, not a DATA-TYPE-TO-FORM mapping --
  Zelazny's framework asks "what are you asserting" before "what form fits the data shape,"
  which is a communicative-claim-first approach, not a data-first approach.
"""


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Distill Minto's Pyramid Principle and Zelazny's Say It With Charts",
        description="Own-words synthesis from real secondary sources, not book text. Connect to Mechanism A.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = stream_complete(
        client, model=MODEL, max_tokens=6000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Real gap caught: neither Barbara Minto's Pyramid Principle "
            "nor Gene Zelazny's Say It With Charts had ever been "
            "referenced or ingested in this project, despite direct "
            "relevance to Sprint 15/16's knowledge-layer work -- "
            "Zelazny's message-to-chart-form mapping is close prior art "
            "for Mechanism A's whole premise, and Minto's pyramid "
            "structure is the actual source for the 'Annotated Pyramid' "
            "seed contract that was specified without knowing where it "
            "came from.\n\n"
            "The founder chose to have you distill the core principles "
            "in your own words from real secondary material (below) "
            "rather than ingest copyrighted book text (a real licensing "
            "concern, consistent with Candidate #11's own on-record "
            "caution about commercial content licensing). Do not quote "
            "the source material at length -- synthesize and cite.\n\n"
            "PRODUCE:\n\n"
            "1. MINTO'S PYRAMID PRINCIPLE, DISTILLED -- the core logic "
            "(SCQA, MECE, vertical/horizontal logic, the four ordering "
            "principles) in your own words, tight enough to be usable as "
            "reference material for this team's own work, not a book "
            "report.\n\n"
            "2. ZELAZNY'S FRAMEWORK, DISTILLED -- the five relationship-"
            "to-chart-form mappings and the message-first principle, in "
            "your own words.\n\n"
            "3. DIRECT CONNECTION TO MECHANISM A. This is the important "
            "part -- do not just summarize, apply. Specifically: (a) "
            "Zelazny's 5 relationship-to-form mappings are a real, "
            "field-validated (40+ years at McKinsey) instance of exactly "
            "what Mechanism A's contracts need in their "
            "'what_it_asserts' / communicative-claim field -- are they "
            "usable as a genuine seed for the STATISTICAL-chart contracts "
            "specifically (component/item/time-series/frequency/"
            "correlation), and if so, how does this relate to or improve "
            "on Draco's cost-ranking approach, which has no equivalent "
            "message-first logic at all? (b) Does Minto's MECE principle "
            "give the Annotated Pyramid contract's composition rule "
            "something more rigorous than what was improvised earlier -- "
            "specifically, should 'spatial-rank-encoding must be "
            "monotonic' be extended or corrected using MECE (the "
            "grouping/exhaustiveness discipline) as a real composition "
            "rule source?\n\n"
            "4. WHAT THIS MEANS FOR THE SOURCE-TIER QUALITY PRIOR. The "
            "team already decided that content from McKinsey/BCG-class "
            "sources gets treated as a high-trust convention prior for "
            "seeding the knowledge base. Zelazny WAS McKinsey's own "
            "Director of Visual Communications and Minto WAS a McKinsey "
            "consultant -- their frameworks are arguably the ARTICULATED "
            "RATIONALE behind why McKinsey-style decks look the way they "
            "do, not just attestation of what forms McKinsey decks use. "
            "Does this change how the source-tier prior should be "
            "understood for McKinsey-originated material specifically -- "
            "is this closer to Candidate #2's 'structured design "
            "knowledge with rationale' than to Candidate #11's 'corpus "
            "with no outcome variable'? Give a direct answer, this "
            "matters for how the knowledge layer's evidence gets tagged.\n\n"
            "5. WHAT IS NOT COVERED. Both frameworks predate the "
            "browser-native/interactive/generative primitives this team "
            "is reaching for (Slider, Carousel, diegetic embedding, "
            "motion). State plainly that neither framework offers "
            "anything for the non-chart-shaped contracts -- don't let "
            "the strength of this material on the chart side create an "
            "impression it also covers the harder, newer part of the "
            "problem.\n\n"
            f"{SOURCE_MATERIAL}\n"
        )}],
    )

    distillation = result.text
    db.log_usage("kenji", result.input_tokens, result.output_tokens)

    db.set_memory("kenji", "minto_zelazny_distillation", distillation)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"minto-zelazny-distillation-task-{task_id}",
        text=distillation,
        metadata={"agent": "kenji", "type": "minto_zelazny_distillation"},
    )
    db.update_task(
        task_id, status="completed", result=distillation,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/minto_zelazny_distillation"},
    )

    print(f"[{NAME}] (continuations: {result.continuations})\n\n{distillation}")
    print(f"\n\n--- {len(distillation)} chars, stored as kenji/minto_zelazny_distillation ---")


if __name__ == "__main__":
    run()
