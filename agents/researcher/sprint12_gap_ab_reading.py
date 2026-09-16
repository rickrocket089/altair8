"""Sprint 12: Kenji reads all 9 Gap A+B papers against one leading question.

Sophie's Sprint 12 proposal (2026-09-16, approved by the founder in live chat)
scoped this deliberately narrow -- not a landscape survey, one leitfrage per
paper: does it supply empirical evidence that discriminates between
"internalized structure" and "convention reproduction" (hypothesis 6 /
backlog #23), and does it bear on C1's novelty claim at all?

Two calls per paper would blow the context budget if done as one giant prompt
(9 full texts run to ~800k characters combined) -- so this reads each paper
individually (full text, focused questions, short output) and then
synthesizes the 9 short verdicts into one answer to the sprint's leitfrage.
Same reason Sprint 8's pipeline passed a SectionContext instead of the whole
document graph between stages: keep each call to what it actually needs.

Per the founder's explicit instruction (2026-09-16 chat): ordinary contrary
findings in individual papers are not escalated -- only a finding that
directly undermines a novelty claim (the C1/TVCG precedent from the day
before) gets flagged for a stop-and-assess.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, fulltext, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"

PAPERS = [
    ("the-rationale-for-rationale", "van Gelder, The rationale for Rationale (2007)", "A"),
    ("compendium-making-meetings-into-knowledge-events",
     "Buckingham Shum & Selvin, Compendium (2001)", "A"),
    ("knowledge-cartography-for-open-sensemaking-communities",
     "Buckingham Shum & Okada, Knowledge Cartography (2008)", "A"),
    ("contested-collective-intelligence",
     "Buckingham Shum et al., Contested Collective Intelligence (2011)", "A"),
    ("argument-mining-a-survey", "Lawrence & Reed, Argument Mining: A Survey (2019)", "A"),
    ("planning-text-for-advisory-dialogues",
     "Moore & Paris, Planning Text for Advisory Dialogues (1993)", "B"),
    ("building-applied-natural-language-generation-systems",
     # Founder-supplied arXiv preprint cmp-lg/9605002 (1996), Reiter SOLO --
     # titled "Building Natural Language Generation Systems", not the 1997
     # Reiter & Dale journal article the acquisition list named. Related,
     # earlier, same primary author -- not the identical source. Flagged so
     # Kenji cites it correctly rather than as "Reiter & Dale 1997."
     "Reiter, Building Natural Language Generation Systems (arXiv preprint, 1996 -- "
     "NOT the 1997 Reiter & Dale journal article originally requested; solo-authored, "
     "earlier, overlapping scope)", "B"),
    ("a-computational-approach-to-politeness",
     "Danescu-Niculescu-Mizil et al., A Computational Approach to Politeness (2013)", "B"),
    ("individual-and-domain-adaptation-in-sentence-planning-for-di",
     "Bangalore & Stent, Individual and Domain Adaptation in Sentence Planning (2007)", "B"),
]

LEITFRAGE = (
    "Does this paper supply empirical evidence that discriminates between "
    "'internalized structure' and 'convention reproduction' as explanations "
    "for audience/goal-sensitive behavior (hypothesis 6 / backlog #23) -- or "
    "does it not bear on that distinction at all? Separately: does anything "
    "in it directly undermine C1's novelty claim (visual weight derived from "
    "author-assigned confidence bound to an epistemic category)? Ordinary "
    "disagreement or a contrary finding on a tangential point is NOT a "
    "novelty flag -- founder's explicit instruction, 2026-09-16 -- only a "
    "finding that shows C1's specific mechanism already exists elsewhere "
    "counts."
)


def _read_one(client: Anthropic, slug: str, label: str, gap: str) -> dict:
    text = fulltext.read(slug)
    with client.messages.stream(
        model=MODEL, max_tokens=1200, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            f"Read this paper in full and answer the sprint's leitfrage for "
            f"it specifically.\n\n{LEITFRAGE}\n\n"
            "Answer in exactly this structure, tight, no padding:\n\n"
            "H6 RELEVANCE: [one sentence -- does it bear on the internalized-"
            "structure-vs-convention-reproduction question, and if so how? "
            "If not, say plainly 'does not bear on this distinction.']\n"
            "C1 IMPLICATION: [one sentence, or 'none.']\n"
            "NOVELTY FLAG: [NONE, or a specific one-sentence statement of "
            "what in this paper directly undermines C1's mechanism -- not a "
            "vague resemblance.]\n"
            "ONE THING WORTH KEEPING: [one sentence -- a finding or "
            "framework from this paper worth remembering regardless of the "
            "above, or 'none.']\n\n"
            f"=== FULL TEXT: {label} ===\n{text}\n"
        )}],
    ) as stream:
        resp = stream.get_final_message()
    db.log_usage("kenji", resp.usage.input_tokens, resp.usage.output_tokens)
    return {"slug": slug, "label": label, "gap": gap, "verdict": resp.content[0].text}


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 12: read Gap A+B (9 papers) against hypothesis 6",
        description="Per-paper leitfrage pass, then synthesis. Sophie's scoped Sprint 12 brief.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    per_paper = []
    for slug, label, gap in PAPERS:
        v = _read_one(client, slug, label, gap)
        per_paper.append(v)
        print(f"[{NAME}] read ({gap}) {label[:60]}")
        print(v["verdict"])
        print("---")

    per_paper_block = "\n\n".join(
        f"[{p['gap']}] {p['label']}\n{p['verdict']}" for p in per_paper
    )

    with client.messages.stream(
        model=MODEL, max_tokens=4000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "You've now read all 9 Gap A+B papers individually against the "
            "sprint's leitfrage. Synthesize -- this is what Sophie and Ingrid "
            "will use to decide whether Backlog #23 (the actual hypothesis-6 "
            "test) is still the right next step, and how.\n\n"
            f"{LEITFRAGE}\n\n"
            "PRODUCE:\n\n"
            "1. DIRECT ANSWER: across all 9 papers, did ANY of them supply "
            "real empirical evidence discriminating internalized structure "
            "from convention reproduction? Most of this literature is about "
            "argument mapping, NLG architecture and politeness theory, not "
            "behavioral testing of models -- say plainly if the honest answer "
            "is 'no, this literature doesn't test that distinction, it's the "
            "wrong kind of evidence for this question' rather than stretching "
            "a paper to fit.\n\n"
            "2. NOVELTY FLAGS: list any paper that raised one, verbatim. If "
            "none did, say so in one line -- don't manufacture drama.\n\n"
            "3. WHAT'S ACTUALLY USEFUL HERE, EVEN IF IT DOESN'T ANSWER H6: "
            "pull the 'one thing worth keeping' from each paper into a short "
            "list -- this is real relevant literature for Altair8 even if it "
            "doesn't resolve the hypothesis-6 question.\n\n"
            "4. WHAT THIS MEANS FOR SPRINT 12'S DSR TRANSITION CRITERION: "
            "Sophie's criterion was (a) backlog #15/#18 closed and (b) the "
            "hypothesis 6 leitfrage has a clear direction. Is (a) satisfied "
            "now? Does (b) have a direction, even if the direction is 'this "
            "literature can't settle it, Backlog #23's own behavioral test "
            "is the only thing that can'?\n\n"
            "5. RECOMMENDATION: what should Sophie propose next -- run "
            "Backlog #23 now, or is there a gap first?\n\n"
            f"=== ALL 9 PER-PAPER READINGS ===\n{per_paper_block}\n"
        )}],
    ) as stream:
        resp = stream.get_final_message()

    synthesis = resp.content[0].text
    db.log_usage("kenji", resp.usage.input_tokens, resp.usage.output_tokens)

    full_brief = (
        f"# Sprint 12: Gap A+B Reading — Hypothesis 6 Leitfrage\n\n"
        f"## Synthesis\n\n{synthesis}\n\n"
        f"---\n\n## Per-Paper Readings\n\n{per_paper_block}\n"
    )

    db.set_memory("kenji", "sprint12_gap_ab_reading", full_brief)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"brief-task-{task_id}",
        text=full_brief,
        metadata={"agent": "kenji", "type": "sprint12_gap_ab_reading"},
    )
    db.update_task(
        task_id, status="completed", result=full_brief,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/sprint12_gap_ab_reading"},
    )

    print(f"[{NAME}]\n\n{synthesis}")
    print(f"\n\n--- {len(full_brief)} chars total, stored as kenji/sprint12_gap_ab_reading ---")


if __name__ == "__main__":
    run()
