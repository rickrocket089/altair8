"""Ingrid audits Sophie's twelve-sprint assessment of where the programme stands.

Not a sprint review. The founder asked, in his own words, where the project
stands and what it has actually proven; Sophie answered him directly, and then
asked for that answer to be checked rather than taken on trust. She wrote the
assessment, so she is the last person who should be its only judge.

Everything is passed whole -- every sprint outcome, both process reviews, the
hypotheses, the design principles, the entire open backlog. Nothing is sliced.
The Sprint 11 close review was run on a truncated brief and produced a finding
about a defect that did not exist, which is a mistake worth making exactly once.

Ingrid's persona already instructs her to verify Sophie's claims against the
database rather than trust them. This is the first time that instruction has
been pointed at a strategic claim rather than a process one.

The assessment below is an English rendering of what the founder was told in
German. The substance is unchanged; where the German hedged, the English
hedges.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.reviewer.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

ASSESSMENT = """
SOPHIE'S ASSESSMENT, AS DELIVERED TO THE FOUNDER (2026-09-15)

## What is actually proven

**1. The gap exists. This is the programme's strongest result, and it is a
negative one.**

Across five sprints and four categories -- commercial tools, foundation-model
providers' own first-party capabilities, open source, academic literature --
Kenji found no system that reasons about visual-form selection at the
presentation level with an explicit audience model. Replicated, from
independent sources, and it survived Ingrid's reviews. The nearest analogues
are measured cleanly: Genially solved the non-linear container but its topology
is 100% author-scripted at creation time; Anthropic's dataviz skill is the most
developed form-reasoning artifact found anywhere in the programme but is scoped
to charts and has no audience model.

Limit: ACM DL, CHI, UIST and InfoVis remain unreached (#15). "Nobody has solved
this" is strictly "nobody in the literatures we could reach".

**2. Base models are not confabulating -- they reason in at least partly
principled ways.**

Sprint 6 (pilot, 3 pairs, 2 models) plus Sprint 7 (6 adversarial pairs, 12
variants, 3 models). The reasoning shifts when goal and audience change, it
discriminates between alternatives, and in the strongest cases the model
switches medium category rather than chart sub-type. Gemini's Sprint 6
form-conservatism did NOT replicate under adversarial pressure.

Limit, named by the team itself: not causally provable from API output, and
Naledi's "culturally-scripted-scenario problem" stands -- where a scenario is a
recognisable professional script, the model may be pattern-matching rather than
reasoning. What is established is something about MODEL BEHAVIOUR, nothing
about communication effect.

**3. It is buildable.** Sprint 8: an agent pipeline produces a real interactive
HTML report. Sprint 9 Phase B: four prototypes in which the generative decision
under test is unavoidable by prompt design. Sprint 11: a deterministic
interface whose visual weight derives from confidence. Feasibility, not
efficacy.

## What is not proven

- the gap exists: ESTABLISHED (conditional on reached literature)
- models reason about form rather than post-hoc rationalising: SUPPORTED, not causal
- a different form COMMUNICATES BETTER: NO EVIDENCE AT ALL
- agentic form-reasoning improves the outcome: NO EVIDENCE AT ALL
- an agent can produce an HONEST audit of itself: UNTESTED (#24)

In twelve sprints, 1017 retrieved papers, six agents and five prototypes, not
one real reader has ever seen any of these artifacts. Every claim about
"communicates better" -- the sentence the north star rests on -- stands on
literature and self-assessment.

The wall has been announcing itself in the record for weeks, always the same
shape: Sprint 9 Phase C deferred (#16, still open). Sprint 10 failed its own
success criterion (b). Sprint 11 produced a design finding -- the confidence
encoding is barely legible in exactly the default state -- that nobody can
settle without letting someone look at it. Backlog #14, "acquire a way to run
human-subject studies", has been open since 2026-08-20 and has never been given
a sprint.

## The meta-finding about the team itself

The founder's first goal was to learn how far a pure AI team gets. The evidence
is mixed and honest: the review gate has genuinely blocked three closes
(Sprints 4, 8, 11) -- it is not ceremony. Agents have named their own
weaknesses unprompted. But Process Review #1's dominant failure mode holds to
this day: rules exist, enforcement does not. Sprint 11 sat still for 26 days
and it was not the process that caught it, it was the founder coming back. Even
today the chain was "founder asks -> verification -> gate fires", not "team
notices".

## Recommendation given to the founder

What remains that still produces knowledge splits into two tracks, and one of
them the team fundamentally cannot do:

TRACK A -- real readers. Not a sprint, an acquisition: a university contact,
Prolific, the founder's own network. Ten to twenty people are enough for a
first real falsification. Until then the team can produce artifacts
indefinitely without ever testing the central thesis. The founder's decision,
not the agents'.

TRACK B -- model behaviour. The part the team can establish alone, and closer
to the thesis than it first appears: "agents must understand WHY a form
communicates better" is a claim about models, measurable over the API. Backlog
#23 (why do models fail at purpose-to-visualization mapping) and #24 (can an
agent produce an honest rather than merely well-formed audit) are both decidable
with no human subjects at all.

Sophie's recommendation: Track B next, specifically #24, because otherwise C1
stays a handsome renderer whose actual question sits untested in the record.
Track A started by the founder in parallel, as procurement rather than a sprint.

Advised against: further polishing of the C1 prototype -- the path of least
resistance, which the team wrote down as Hypothesis 4 about itself.

CORRECTION, made before this audit was commissioned: Sophie told the founder
"seven of the 23 open backlog items are now prototype polish -- the drift,
visible in numbers". That was wrong. Counting the actual list, three are
(#26, #27, #28), and Sophie created all three herself today on Ingrid's own
instruction from the Sprint 11 review. The numerical evidence for the drift
claim does not hold. Whether the drift claim survives on other grounds is one
of the things this audit is being asked to decide.
"""


def run() -> None:
    require_tool("ingrid", "write_review")
    db.set_memory("ingrid", "status", "online")

    sprints = db.list_sprints()
    outcomes = "\n\n".join(
        f"--- Sprint {s['sprint_number']} ({s['status']}) ---\n"
        f"QUESTION: {s['question']}\n\nOUTCOME: {s['outcome']}"
        for s in sorted(sprints, key=lambda s: s["sprint_number"])
        if s["status"] == "completed"
    )
    backlog = "\n".join(
        f"  #{i['id']} [{i['priority']}] {i['title']} :: {i['description'][:300]}"
        for i in db.list_backlog_items() if i["status"] == "open"
    )
    reviews = db.list_process_reviews()
    process = "\n\n".join(
        f"--- Process Review #{r['id']}, Sprints {r['covers_sprint_from']}-"
        f"{r['covers_sprint_to']} ---\n{r['findings']}" for r in reviews
    )
    strategy = "\n\n".join(
        f"--- {k} ---\n{db.get_memory('team_leader', k)}"
        for k in ("north_star", "hypotheses", "design_principles")
    )

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="ingrid",
        title="Audit: Sophie's twelve-sprint programme assessment",
        description="Founder-commissioned. Not a sprint gate -- an audit of a strategic claim.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "The founder asked Sophie where the programme stands after twelve "
            "sprints and what it has actually proven, because he is deciding "
            "where to go next. She answered him. Then she asked for her answer "
            "to be audited rather than trusted, and he commissioned this.\n\n"
            "This is not a sprint gate. Nothing is blocked by your verdict. "
            "What is at stake is a founder's decision about direction resting "
            "on a summary written by the person who ran the thing being "
            "summarised. Your persona already tells you to verify Sophie's "
            "claims against the database rather than accept them. Do that here, "
            "claim by claim, against the full record below -- every sprint "
            "outcome, both process reviews, the hypotheses, the design "
            "principles, the whole open backlog. Nothing has been sliced.\n\n"
            "Judge:\n\n"
            "1. IS EACH 'PROVEN' CLAIM ACTUALLY PROVEN? Take the three in turn. "
            "For each, say whether the record supports it at the strength "
            "Sophie gives it, and name what would falsify it. Claim 2 is the "
            "one to press hardest: 'base models are not confabulating' rests on "
            "two behavioural tests with small n, one of which Naledi herself "
            "partly disowned. Is 'supported, not causal' the right strength, or "
            "is it still an overclaim?\n\n"
            "2. IS THE FRAMING HONEST, OR IS IT DRAMATISED? 'Not one real "
            "reader in twelve sprints' is rhetorically strong. Is it the "
            "correct crux, or does it flatten a programme that was never "
            "supposed to have readers yet -- most of it was literature review "
            "and Define-Objectives work, where having no readers is not a "
            "failure? Say plainly if Sophie has over-dramatised her own record. "
            "Note that she has already withdrawn one numerical claim (seven "
            "prototype-polish items; the real count is three, all created by "
            "her today on your instruction). Does that withdrawal take the "
            "drift argument with it, or does the drift claim survive on other "
            "evidence in the record?\n\n"
            "3. WHAT IS MISSING FROM THE ASSESSMENT? Something established in "
            "twelve sprints that she left out, or something unestablished she "
            "let pass as established. Check especially whether the candidate "
            "approaches, the Sprint 10 concept work and the Sprint 6-7 "
            "behavioural findings are represented fairly or shaped to fit her "
            "conclusion.\n\n"
            "4. IS THE RECOMMENDATION RIGHT? She proposes #24 as the next "
            "sprint and human-subject access as founder procurement, and "
            "advises against more prototype work. Argue the other side properly "
            "before you agree or disagree: there is a real case that #23 (why "
            "models fail at purpose-to-visualization mapping) is the more "
            "fundamental question, and a real case that C1 should be finished "
            "to the point where it could be put in front of readers the moment "
            "Track A opens -- otherwise Track A arrives and there is nothing "
            "ready to test. Which sequencing actually serves the founder?\n\n"
            "5. THE META-FINDING. Sophie writes that the team still does not "
            "catch its own failures and that today's chain was 'founder asks, "
            "verification happens, gate fires'. You are part of what is being "
            "assessed there. Is her account of the team's self-catch capability "
            "accurate, generous, or harsh?\n\n"
            "Write for the founder, not for Sophie. If the assessment is "
            "substantially sound, say so without padding it; if it is not, be "
            "specific about which parts he should not act on.\n\n"
            f"=== SOPHIE'S ASSESSMENT ===\n{ASSESSMENT}\n\n"
            f"=== ALL SPRINT OUTCOMES (complete) ===\n{outcomes}\n\n"
            f"=== NORTH STAR, HYPOTHESES, DESIGN PRINCIPLES ===\n{strategy}\n\n"
            f"=== OPEN BACKLOG (all {len(backlog.splitlines())} items) ===\n{backlog}\n\n"
            f"=== PROCESS REVIEWS (complete) ===\n{process}\n"
        )}],
    ) as stream:
        response = stream.get_final_message()

    audit = response.content[0].text
    db.log_usage("ingrid", response.usage.input_tokens, response.usage.output_tokens)

    db.set_memory("ingrid", "programme_assessment_audit", audit)
    vectorstore.remember(
        collection_name="reviewer_memory",
        doc_id=f"review-task-{task_id}",
        text=audit,
        metadata={"agent": "ingrid", "type": "programme_assessment_audit"},
    )
    db.update_task(
        task_id, status="completed", result=audit,
        artifact_type="review",
        artifact_payload={"memory_key": "ingrid/programme_assessment_audit"},
    )

    print(f"[{NAME}]\n\n{audit}")
    print(f"\n\n--- {len(audit)} chars, stored as ingrid/programme_assessment_audit ---")


if __name__ == "__main__":
    run()
