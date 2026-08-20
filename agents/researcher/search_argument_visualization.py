"""Sprint 11 gate 1: the targeted argument-visualization prior-art search.

Ingrid's condition 1 on the Sprint 10 close. C1 is now the chosen direction, and
Priya flagged -- against her own concept, unprompted, after Kenji had already
finished verifying -- that argument-mapping tools in the HCI literature
(Rationale, Compendium, CHI/UIST argumentation interfaces) were never retrieved.
Kenji did not catch this gap.

Ingrid's ruling: it blocks neither the close nor the build, but it must run
before C1's novelty claim is presented anywhere externally. If those tools
implement confidence-weighted visual encoding derived from epistemic category
classification, C1's restated claim narrows again -- possibly to nothing.

Real retrieval, same discipline as Sprint 10: Kenji designs the queries,
tools.papers runs them, Kenji verifies against what actually came back and
separates recollection from retrieval.

Known limitation going in, and the reason this gap exists at all: much of this
literature is in ACM venues the team's four sources reach poorly, and ACM DL
has no free API. That is backlogged as a capability item. This search is what
can be done meanwhile, not a substitute for it.
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

NAMED_TARGETS = """Ingrid and Priya between them named these specific targets:
  - Rationale (argument-mapping software, van Gelder)
  - Compendium (issue-based information system / dialogue mapping tool)
  - CHI / UIST work on argument visualization interfaces
  - Toulmin-schema implementations with confidence weighting
  - "minimum spanning argument" as a concept in rhetoric or argumentation"""


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    concepts = db.get_memory("priya", "sprint10_concepts_blind") or ""
    restated = db.get_memory("priya", "sprint10_restated_claims") or ""
    m = re.search(r"#\s*CONCEPT 1:.*?(?=^#\s*CONCEPT 2:)", concepts, re.S | re.M)
    c1 = m.group(0) if m else concepts[:8000]

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 11 gate 1: argument-visualization prior-art search for C1",
        description="Ingrid condition 1. Must run before C1's claim is presented externally.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    with client.messages.stream(
        model=MODEL, max_tokens=2500, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "A gap in your Sprint 10 verification needs closing. C1 (The "
            "Commitment Audit) is now the team's chosen direction, and the "
            "concept's own designer flagged -- unprompted, against her own "
            "interest -- that you never retrieved the argument-mapping "
            "literature in HCI. She is right.\n\n"
            f"{NAMED_TARGETS}\n\n"
            "Design 8 queries to close this. Design around three things:\n"
            "1. These tools are older (1990s-2000s) and partly commercial. "
            "Query the academic work ABOUT them, not product names alone.\n"
            "2. The specific mechanism at issue is not argument mapping in "
            "general -- it is whether any system derives VISUAL WEIGHT from a "
            "CONFIDENCE SCORE attached to an EPISTEMIC CATEGORY "
            "(evidence / inference / assumption / assertion). Argument mapping "
            "existing is not the threat; that specific encoding is.\n"
            "3. Much of this is in CHI and UIST, which our sources index "
            "unevenly. Prefer terms likely to appear in arXiv preprints or in "
            "papers that cite this tradition.\n\n"
            f"C1 AS SPECIFIED:\n{c1[:7000]}\n\n"
            'Return ONLY a JSON array of 8 query strings. No prose, no fences.'
        )}],
    ) as stream:
        qresp = stream.get_final_message()
    db.log_usage("kenji", qresp.usage.input_tokens, qresp.usage.output_tokens)

    raw = re.sub(r"^```(?:json)?|```$", "", qresp.content[0].text.strip(), flags=re.M).strip()
    queries = json.loads(raw)
    print(f"[{NAME}] {len(queries)} queries designed.")

    retrieval = []
    for q in queries:
        try:
            hits = papers.search_all_sources(q, max_results_per_source=RESULTS_PER_SOURCE)
        except Exception as exc:
            print(f"[{NAME}]   FAILED '{q[:50]}': {exc}")
            hits = []
        retrieval.append({"query": q, "count": len(hits), "hits": hits})
        print(f"[{NAME}]   '{q[:64]}...' -> {len(hits)}")
        time.sleep(2)

    total = sum(r["count"] for r in retrieval)
    evidence = "\n\n".join(
        f"QUERY: {r['query']}  ({r['count']} results)\n" + "\n".join(
            f"  - [{h.get('source','?')}] {h.get('title','(untitled)')}\n"
            f"    {(h.get('abstract') or '')[:600]}" for h in r["hits"]
        ) for r in retrieval
    )

    with client.messages.stream(
        model=MODEL, max_tokens=10000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Your queries have been run. Verdict on C1, please.\n\n"
            "Ground rule, unchanged: verify against retrieved evidence, label "
            "recollection as recollection, never describe a check you did not "
            "perform.\n\n"
            f"C1 AS SPECIFIED:\n{c1[:7000]}\n\n"
            f"C1'S RESTATED CLAIM (post-Sprint 10):\n{restated[:6000]}\n\n"
            f"RETRIEVED EVIDENCE:\n{evidence}\n\n"
            "PRODUCE:\n"
            "1. Retrieval log (S3): queries, returned, retained, noise rate, "
            "and whether this depth is proportionate to the verdict.\n"
            "2. THE DIRECT QUESTION: does any retrieved system derive visual "
            "weight from a confidence score attached to an epistemic category "
            "classification? Yes or no, with citation. This is the one that "
            "matters -- argument mapping existing does not threaten C1; that "
            "specific encoding does.\n"
            "3. Does anything retrieved threaten the minimum-spanning-argument "
            "scaffold as a distinct contribution?\n"
            "4. Revised verdict on C1's restated claim: does it survive, "
            "narrow further, or fall? If the honest answer is that ACM-indexed "
            "literature could still overturn this and you cannot reach it, say "
            "that plainly rather than issuing a verdict the evidence does not "
            "support.\n"
            "5. What C1's public description must acknowledge as a result."
        )}],
    ) as stream:
        vresp = stream.get_final_message()

    verdict = vresp.content[0].text
    db.log_usage("kenji", vresp.usage.input_tokens, vresp.usage.output_tokens)

    for r in retrieval:
        for h in r["hits"]:
            try:
                papers.save_paper(h)
            except Exception:
                pass

    db.set_memory("kenji", "c1_argument_visualization_check", verdict)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"c1-argviz-task-{task_id}", text=verdict,
        metadata={"agent": "kenji", "type": "prior_art_check", "sprint": 11, "concept": "C1"},
    )
    db.update_task(
        task_id, status="completed", result=verdict,
        artifact_type="prior_art_verification",
        artifact_payload={"memory_key": "kenji/c1_argument_visualization_check",
                          "queries_run": len(queries), "results_retrieved": total},
    )

    print(f"[{NAME}]\n\n{verdict}")


if __name__ == "__main__":
    run()
