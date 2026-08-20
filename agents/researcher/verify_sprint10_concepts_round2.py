"""Sprint 10, Pass 3 round 2: redirected retrieval after Kenji called round 1 inadequate.

Round 1 ran 18 queries for ~376 results and retained ~13 (96.5% noise). Kenji's
own proportionality judgement was that the retrieval was inadequate for
confident verdicts on Concepts 2, 3, 4 and 6 -- the query vocabulary was not
reaching the relevant literature. He ended his brief with specific redirections.

Rather than transcribe those redirections by hand, this asks Kenji to redesign
his own queries from his round-1 retrieval log -- he can see which framings
returned nothing and why, which is better information than a copied list.

Known limit going in, which he named himself: the most important prior art here
is book-length (Bertin 1967, Wilkinson's Grammar of Graphics, Munzner 2014) and
these APIs index papers, not books. Queries should therefore target papers that
cite, implement or extend that tradition -- Mackinlay's APT (1986) being the
specific precursor he flagged as most likely to change a verdict. That
instruction is given to him explicitly below.

Round 1's verdicts are preserved at kenji/sprint10_concept_verification_round1
before this overwrites the current key.
"""
import json
import os
import re
import time

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher.persona import NAME, SYSTEM_PROMPT
from tools import db, papers, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

MODEL = "claude-sonnet-4-6"
RESULTS_PER_SOURCE = 10

# Concepts 2, 3, 4 and 6 were the inadequate ones. 1 and 5 get one query each
# to test whether a redirected vocabulary changes an already-grounded verdict.
QUERY_BUDGET = {"1": 2, "2": 4, "3": 5, "4": 3, "5": 2, "6": 5}


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    round1 = db.get_memory("kenji", "sprint10_concept_verification") or ""
    if not round1:
        raise SystemExit("No round 1 verification found.")

    if not db.get_memory("kenji", "sprint10_concept_verification_round1"):
        db.set_memory("kenji", "sprint10_concept_verification_round1", round1)
        print(f"[{NAME}] Round 1 preserved at kenji/sprint10_concept_verification_round1")

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 10 Pass 3 round 2: redirected prior-art retrieval",
        description="Requery after round 1 was judged inadequate for 4 of 6 concepts.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    budget_text = ", ".join(f"concept {k}: {v} queries" for k, v in QUERY_BUDGET.items())

    # ---------- Stage 1: Kenji redesigns his own queries ----------
    with client.messages.stream(
        model=MODEL,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "This is round 2 of your Sprint 10 prior-art verification. You "
            "judged round 1 inadequate for Concepts 2, 3, 4 and 6, and ended "
            "your brief with specific redirections. Redesign the queries now, "
            "using your own retrieval log to see which framings returned "
            "nothing and why.\n\n"
            "Query budget for this round: " + budget_text + ". Concepts 1 and 5 "
            "already have grounded verdicts and get a small budget only to test "
            "whether a redirected vocabulary overturns them.\n\n"
            "Three things to design around:\n\n"
            "1. Your round-1 vocabulary described the concepts in OUR language. "
            "Search the language the relevant field actually uses. Where a "
            "field has a standard term for something we invented a phrase for, "
            "use theirs.\n\n"
            "2. The most important prior art you named is book-length -- Bertin "
            "1967, Wilkinson's Grammar of Graphics, Munzner 2014. These APIs "
            "index papers, not books. Target papers that CITE, IMPLEMENT or "
            "EXTEND that tradition instead. Mackinlay's APT (1986) is a paper "
            "and you flagged it as the precursor most likely to change a "
            "verdict -- make sure a query can actually reach it.\n\n"
            "3. Much of what you want sits in CHI, UIST and IEEE VIS. Our "
            "sources index those unevenly and ACM's library is not available "
            "to us at all. Where you expect a venue we cannot reach, prefer "
            "query terms likely to appear in arXiv preprints of the same work.\n\n"
            "YOUR ROUND 1 BRIEF (retrieval log and verdicts):\n\n"
            f"{round1[:30000]}\n\n"
            "Return ONLY a JSON object mapping concept number to its list of "
            "queries, no prose, no code fences:\n"
            '{"1": ["..."], "2": ["..."], "3": ["..."], "4": ["..."], '
            '"5": ["..."], "6": ["..."]}'
        )}],
    ) as stream:
        qresp = stream.get_final_message()
    db.log_usage("kenji", qresp.usage.input_tokens, qresp.usage.output_tokens)

    raw = re.sub(r"^```(?:json)?|```$", "", qresp.content[0].text.strip(),
                 flags=re.MULTILINE).strip()
    query_map = json.loads(raw)
    planned = sum(len(v) for v in query_map.values())
    print(f"[{NAME}] Round 2: {planned} redirected queries across "
          f"{len(query_map)} concepts.")

    # ---------- Stage 2: run them ----------
    retrieval, failures = {}, []
    for num, queries in query_map.items():
        retrieval[num] = []
        for q in queries:
            try:
                hits = papers.search_all_sources(q, max_results_per_source=RESULTS_PER_SOURCE)
            except Exception as exc:
                failures.append(f"concept {num} / '{q}': {type(exc).__name__}: {exc}")
                hits = []
            retrieval[num].append({"query": q, "count": len(hits), "hits": hits})
            print(f"[{NAME}]   c{num}: '{q[:62]}...' -> {len(hits)}")
            time.sleep(2)

    total = sum(e["count"] for v in retrieval.values() for e in v)
    print(f"[{NAME}] {total} results retrieved this round.")

    # ---------- Stage 3: revised verdicts ----------
    evidence = "\n\n".join(
        f"===== ROUND 2 EVIDENCE, CONCEPT {num} =====\n" + "\n\n".join(
            f"QUERY: {e['query']}  ({e['count']} results)\n" + "\n".join(
                f"  - [{h.get('source','?')}] {h.get('title','(untitled)')}\n"
                f"    {(h.get('abstract') or '')[:600]}"
                for h in e["hits"]
            )
            for e in entries
        )
        for num, entries in retrieval.items()
    )
    failure_note = ("WHOLE-QUERY FAILURES:\n" + "\n".join(failures)) if failures else \
        "No whole-query failures this round."

    with client.messages.stream(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Round 2 evidence is in. Revise your verdicts.\n\n"
            "Same ground rule as round 1, and it matters more now: verify "
            "against retrieved evidence. Where you rely on recollection, label "
            "it as recollection. Do not describe a check you did not perform.\n\n"
            f"YOUR ROUND 1 BRIEF:\n\n{round1[:30000]}\n\n"
            f"{evidence}\n\n{failure_note}\n\n"
            "PRODUCE:\n\n"
            "1. A ROUND 2 RETRIEVAL LOG (S3): queries, results returned, "
            "retained, noise rate. Then a direct answer: is the combined "
            "round 1 + round 2 retrieval now proportionate to the verdicts you "
            "are giving? Name any concept where it still is not. Do not soften "
            "this because a second round has been spent on it.\n\n"
            "2. REVISED VERDICT PER CONCEPT (all six). For each, state "
            "explicitly whether round 2 CHANGED, STRENGTHENED or LEFT UNCHANGED "
            "your round 1 verdict, and why. A verdict that moved is the most "
            "valuable output of this round -- do not bury it.\n\n"
            "3. THE APT QUESTION. You flagged Mackinlay's APT (1986) as the "
            "precursor most likely to change Concept 3's verdict. Did round 2 "
            "reach it or work that describes it? State plainly what this "
            "evidence does to Concept 3's novelty claim, including if the "
            "answer is that the concept's claim does not survive.\n\n"
            "4. A closing recommendation to Sophie: which concepts are now "
            "safe to carry into a synthesis the founder will choose from, "
            "which carry a novelty claim that must be restated before it is "
            "shown to anyone, and which need prior-art work this team cannot "
            "currently perform with the sources it has."
        )}],
    ) as stream:
        vresp = stream.get_final_message()

    verification = vresp.content[0].text
    db.log_usage("kenji", vresp.usage.input_tokens, vresp.usage.output_tokens)

    for v in retrieval.values():
        for e in v:
            for h in e["hits"]:
                try:
                    papers.save_paper(h)
                except Exception:
                    pass

    db.set_memory("kenji", "sprint10_concept_verification", verification)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"sprint10-pass3-round2-task-{task_id}",
        text=verification,
        metadata={"agent": "kenji", "type": "concept_verification", "sprint": 10, "round": 2},
    )
    db.update_task(
        task_id, status="completed", result=verification,
        artifact_type="prior_art_verification",
        artifact_payload={
            "memory_key": "kenji/sprint10_concept_verification",
            "round": 2,
            "queries_run": planned,
            "results_retrieved": total,
        },
    )

    print(f"[{NAME}]\n\n{verification}")
    print(f"\n\n--- {len(verification)} chars ---")


if __name__ == "__main__":
    run()
