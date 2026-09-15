"""Kenji reads the first human-subject study this project has ever had access to.

"I'm Not Sure, But...": Examining the Impact of Large Language Models'
Uncertainty Expression on User Reliance and Trust. ACM FAccT 2024,
doi 10.1145/3630106.3658941. Full text supplied by the founder on 2026-09-15
because dl.acm.org refuses automated clients.

Why this one matters more than its novelty relevance. Across twelve sprints
this team has never put an artifact in front of a reader, and Ingrid's audit
on 2026-09-15 named that as the wall the programme keeps arriving at. Armstrong
et al. -- a year of funded work on exactly this problem -- turned out to have
run no controlled study either, only design-team co-evaluation. So the entire
question of whether admitted uncertainty actually changes anything for the
person reading has, until now, been answered by nobody in our record.

This paper ran the experiment. That makes it the closest thing to reader
evidence Altair8 possesses, and it bears directly on C1's premise: C1 shows a
reader that a claim is weakly supported. Nobody here has ever checked what a
reader does with that information.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, fulltext, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"
SLUG = "im-not-sure-but-examining-the-impact-of-llm-uncertainty-expr"


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    paper = fulltext.read(SLUG)
    armstrong = db.get_memory("kenji", "armstrong_fulltext_verdict") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Read the uncertainty-expression reliance study in full",
        description="First human-subject evidence available to this project. Founder-supplied.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model=MODEL, max_tokens=16000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Full text below, supplied by the founder. Read it for what it "
            "measures, not for whether it threatens anything -- this is not a "
            "novelty check.\n\n"
            "Context for why this matters more than it looks. In twelve "
            "sprints this team has never put an artifact in front of a reader. "
            "Armstrong et al., which you read an hour ago, ran a year of funded "
            "work and also ran no controlled study -- only design-team "
            "co-evaluation. So whether admitted uncertainty changes anything "
            "for the person reading has been answered by nobody in our record. "
            "This paper ran the experiment.\n\n"
            "C1's entire premise is that a reader is better served by seeing "
            "that a claim is weakly supported. Nobody here has ever checked "
            "what a reader does with that.\n\n"
            "ANSWER:\n\n"
            "1. THE STUDY DESIGN, precisely. How many participants, recruited "
            "how, doing what task, in which conditions, measured on what. If "
            "there were several studies, separate them. Give the numbers, not "
            "an impression of the numbers.\n\n"
            "2. WHAT EXPRESSING UNCERTAINTY ACTUALLY DID. Direction and size "
            "of the effects on reliance, on trust, and on accuracy if "
            "measured. Where an effect was absent or went the wrong way, say "
            "so as prominently as where it worked.\n\n"
            "3. DID THE FORM OF EXPRESSION MATTER? If they compared ways of "
            "expressing uncertainty -- first person versus general, numerical "
            "versus verbal, or any other contrast -- report what differed. "
            "This is the part closest to a design instruction for us.\n\n"
            "4. BACKFIRE EFFECTS. Anything showing that admitting uncertainty "
            "hurt -- lower perceived competence, disengagement, worse "
            "outcomes, or reliance moving the wrong way. Look for this "
            "specifically. A result that complicates C1 is worth more to us "
            "than one that flatters it.\n\n"
            "5. WHAT IT PREDICTS FOR C1. C1 renders a claim as 'weakly "
            "supported' with reduced visual weight. On this evidence, what "
            "should we expect a reader to do -- discount that claim, discount "
            "the whole document, disengage, or nothing measurable? Be explicit "
            "about how far the transfer is defensible: their stimulus is "
            "conversational LLM text, ours is a rendered argument map, and "
            "those are different enough that the extrapolation needs stating "
            "rather than assuming.\n\n"
            "6. WHAT IT SAYS ABOUT THE PROGRAMME'S UNSTATED BET B. Ingrid "
            "named a bet nobody had stated: that the person commissioning a "
            "document and the person reading it want compatible things, when "
            "form may partly perform credibility for the sender. Does this "
            "study bear on that? Specifically -- if admitted uncertainty "
            "improves reader calibration but lowers perceived competence of "
            "the source, that tension is measured here rather than "
            "speculated.\n\n"
            "7. LIMITS. Population, task, domain, and anything that makes this "
            "weaker evidence for business communication than it first appears. "
            "Then say plainly what it would take for this team to run the "
            "equivalent study on C1, and whether their design is one we could "
            "adapt rather than invent.\n\n"
            f"YOUR ARMSTRONG VERDICT, for continuity:\n{armstrong[:8000]}\n\n"
            f"=== FULL TEXT ===\n{paper}\n"
        )}],
    ) as stream:
        resp = stream.get_final_message()

    brief = resp.content[0].text
    db.log_usage("kenji", resp.usage.input_tokens, resp.usage.output_tokens)

    db.set_memory("kenji", "uncertainty_reliance_study_brief", brief)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"brief-task-{task_id}",
        text=brief,
        metadata={"agent": "kenji", "type": "uncertainty_reliance_study_brief"},
    )
    db.update_task(
        task_id, status="completed", result=brief,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/uncertainty_reliance_study_brief"},
    )

    print(f"[{NAME}]\n\n{brief}")
    print(f"\n\n--- {len(brief)} chars, stored as kenji/uncertainty_reliance_study_brief ---")


if __name__ == "__main__":
    run()
