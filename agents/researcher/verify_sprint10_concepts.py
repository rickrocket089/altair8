"""Sprint 10, Pass 3: Kenji verifies each concept against real prior art.

THIS RUNS REAL SEARCHES. It does not ask Kenji whether something exists and
trust the answer. Ingrid's own Sprint 10 design review asserted a database
cross-check she had no means to perform -- an instruction that exceeded the
agent's actual capability produced fluent confabulation of compliance rather
than an error. A novelty check built the same way would be worthless, and this
whole sprint exists to avoid exactly that.

Three stages:
  1. Kenji reads the six concepts and proposes search queries for each.
  2. This script runs them for real via tools.papers.search_all_sources
     (arXiv, Semantic Scholar, OpenAlex, IEEE Xplore -- individual source
     failures tolerated and reported, not hidden).
  3. Kenji verifies each concept against what actually came back, and writes
     the Retrieval Log that process action S3 requires.

BLINDING, HONESTLY SCOPED. Kenji is not told which pass a concept came from.
Concept 6's provenance preamble is cut mechanically. But Ingrid predicted in
her design review that blinding would degrade -- concepts self-identify through
vocabulary and through explicit references some of them contain. Rather than
pretend otherwise, the prompt tells Kenji the blinding is imperfect and asks
him to hold a constant standard regardless. Her recommended fix (a
self-identification field in his verdict) was not applied -- founder decision --
so this limitation is disclosed rather than measured.
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
QUERIES_PER_CONCEPT = 3
RESULTS_PER_SOURCE = 8


def collect_concepts() -> list[dict]:
    """Six concepts, provenance preamble stripped from the one that has it."""
    blind = db.get_memory("priya", "sprint10_concepts_blind") or ""
    sighted = db.get_memory("priya", "sprint10_concepts_sighted") or ""

    out = []
    titles = list(re.finditer(r"^#\s*CONCEPT\s+(\d+):\s*(.+)$", blind, re.MULTILINE))
    for i, m in enumerate(titles):
        end = titles[i + 1].start() if i + 1 < len(titles) else len(blind)
        out.append({
            "number": m.group(1),
            "title": m.group(2).strip(),
            "body": blind[m.end():end].strip(),
        })

    # Concept 6 lives in the sighted pass. Cut everything before its first
    # template field -- that preamble names its origin explicitly.
    m6 = re.search(r"###\s*NEW CONCEPT 6:\s*(.+)", sighted)
    if m6:
        after = sighted[m6.end():]
        start = after.find("**1. WHAT WOULD WE BUILD**")
        if start != -1:
            out.append({
                "number": "6",
                "title": m6.group(1).strip(),
                "body": after[start:start + 12000].strip(),
            })
    return out


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    concepts = collect_concepts()
    if len(concepts) < 6:
        print(f"[{NAME}] WARNING: only {len(concepts)} concepts extracted.")
    print(f"[{NAME}] Verifying {len(concepts)} concepts.")

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Sprint 10 Pass 3: per-concept prior-art verification",
        description=f"Real literature search across 4 sources for {len(concepts)} concepts.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    concept_blocks = "\n\n".join(
        f"===== CONCEPT {c['number']}: {c['title']} =====\n{c['body']}" for c in concepts
    )

    # ---------- Stage 1: Kenji proposes the queries ----------
    with client.messages.stream(
        model=MODEL,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Sprint 10 Pass 3. Six proposed concepts for an agent-generated "
            "communication layer need prior-art verification. Before any "
            "searching happens, propose the queries.\n\n"
            f"For EACH concept, give exactly {QUERIES_PER_CONCEPT} search "
            "queries that would surface prior art if it exists. Aim them at "
            "the MECHANISM, not the branding -- a concept's name is ours and "
            "will not appear in anyone's literature. Vary the framing across "
            "the three so a single vocabulary mismatch does not produce a "
            "false negative.\n\n"
            "These go to arXiv, Semantic Scholar, OpenAlex and IEEE Xplore, so "
            "write them as academic search strings, not questions.\n\n"
            f"{concept_blocks}\n\n"
            "Return ONLY a JSON object, no prose, no code fences:\n"
            '{"1": ["query", "query", "query"], "2": [...], ..., "6": [...]}'
        )}],
    ) as stream:
        qresp = stream.get_final_message()
    db.log_usage("kenji", qresp.usage.input_tokens, qresp.usage.output_tokens)

    raw = qresp.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    query_map = json.loads(raw)
    print(f"[{NAME}] Queries proposed for {len(query_map)} concepts.")

    # ---------- Stage 2: run the searches for real ----------
    retrieval = {}
    source_failures = []
    for num, queries in query_map.items():
        retrieval[num] = []
        for q in queries:
            try:
                hits = papers.search_all_sources(q, max_results_per_source=RESULTS_PER_SOURCE)
            except Exception as exc:  # a whole-query failure, not a per-source one
                source_failures.append(f"concept {num} / '{q}': {type(exc).__name__}: {exc}")
                hits = []
            retrieval[num].append({"query": q, "count": len(hits), "hits": hits})
            print(f"[{NAME}]   concept {num}: '{q[:60]}...' -> {len(hits)} results")
            time.sleep(2)  # Semantic Scholar 429s without this

    total = sum(h["count"] for v in retrieval.values() for h in v)
    print(f"[{NAME}] {total} total results retrieved across "
          f"{sum(len(v) for v in retrieval.values())} queries.")

    # ---------- Stage 3: Kenji verifies against what came back ----------
    evidence_parts = []
    for c in concepts:
        num = c["number"]
        blocks = []
        for entry in retrieval.get(num, []):
            lines = [f"QUERY: {entry['query']}  ({entry['count']} results)"]
            for h in entry["hits"]:
                title = h.get("title", "(untitled)")
                src = h.get("source", "?")
                abstract = (h.get("abstract") or "")[:600]
                lines.append(f"  - [{src}] {title}\n    {abstract}")
            blocks.append("\n".join(lines))
        evidence_parts.append(
            f"===== EVIDENCE FOR CONCEPT {num}: {c['title']} =====\n"
            + ("\n\n".join(blocks) if blocks else "(no results returned)")
        )
    evidence = "\n\n".join(evidence_parts)

    failure_note = (
        "SOURCE FAILURES DURING THIS RUN:\n" + "\n".join(source_failures)
        if source_failures else
        "No whole-query failures. Individual sources may still have returned "
        "nothing; search_all_sources tolerates per-source errors silently, so "
        "absence of results for one source is not distinguishable from that "
        "source failing. Treat that as a limit on this retrieval."
    )

    with client.messages.stream(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Sprint 10 Pass 3, verification stage. Your queries have been run "
            "for real against arXiv, Semantic Scholar, OpenAlex and IEEE "
            "Xplore. Below are the concepts and what actually came back.\n\n"
            "Ground rule: verify against the retrieved evidence. Where you "
            "believe prior art exists that this retrieval did not surface, you "
            "may say so -- but label it explicitly as your own recollection, "
            "not as a retrieval finding. Do not describe a check you did not "
            "perform. That distinction is the whole point of this pass.\n\n"
            "A note on blinding: you are deliberately not told which of these "
            "concepts were generated with access to the team's existing "
            "research leads and which were generated without it. That blinding "
            "is imperfect -- some concepts contain references that give it "
            "away. Hold the same verification standard regardless of what you "
            "can infer.\n\n"
            f"{concept_blocks}\n\n"
            f"{evidence}\n\n"
            f"{failure_note}\n\n"
            "PRODUCE:\n\n"
            "1. A RETRIEVAL LOG (process action S3, mandatory): queries run, "
            "results returned, results retained as relevant, the noise rate, "
            "and an explicit judgement on whether this retrieval depth is "
            "proportionate to the claims you are about to make. If it is not, "
            "say so -- an inadequate search honestly reported is worth more "
            "than a confident verdict resting on nothing.\n\n"
            "2. PER CONCEPT, a verdict on the novelty claim:\n"
            "   - NOT NOVEL (this exists; name it)\n"
            "   - PARTIALLY NOVEL (adjacent work exists; state precisely what "
            "     is and is not covered by it)\n"
            "   - NO PRIOR ART FOUND (distinguish clearly: nothing was found, "
            "     which is not the same as nothing existing)\n"
            "   Cite specific retrieved papers where they apply. Cover all "
            "four scope categories at verification depth: third-party tools, "
            "foundation-model-native capabilities, open-source frameworks, "
            "academic research.\n\n"
            "3. THREE SPECIFIC PROBES the reviewer required:\n"
            "   a. Concept 3's primitive vocabulary (position, scale, "
            "      proximity, containment, sequence, path) against the "
            "      visualization GRAMMAR literature specifically -- Bertin's "
            "      Semiologie Graphique, Wilkinson's Grammar of Graphics, "
            "      Munzner -- not just tool implementations. Is the selection "
            "      mechanism differentiated from that tradition, or is it "
            "      chart-type selection one abstraction level up?\n"
            "   b. Do Concepts 1 and 4 collapse into the same prior art "
            "      (argument mapping tools, decision-support systems), making "
            "      them less distinct than they appear?\n"
            "   c. Concept 2's audience simulation: is there prior art on "
            "      LLMs simulating audience response as a generative input, "
            "      and does any of it address whether such a simulation is "
            "      confabulation-prone?\n\n"
            "4. A short closing section: which concept has the strongest "
            "novelty position on this evidence, which the weakest, and what "
            "you would need to search next to raise your confidence."
        )}],
    ) as stream:
        vresp = stream.get_final_message()

    verification = vresp.content[0].text
    db.log_usage("kenji", vresp.usage.input_tokens, vresp.usage.output_tokens)

    for v in retrieval.values():
        for entry in v:
            for h in entry["hits"]:
                try:
                    papers.save_paper(h)
                except Exception:
                    pass

    db.set_memory("kenji", "sprint10_concept_verification", verification)
    db.set_memory("kenji", "sprint10_retrieval_raw", json.dumps(
        {k: [{"query": e["query"], "count": e["count"]} for e in v] for k, v in retrieval.items()},
        indent=2,
    ))
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"sprint10-pass3-task-{task_id}",
        text=verification,
        metadata={"agent": "kenji", "type": "concept_verification", "sprint": 10, "pass": 3},
    )
    db.update_task(
        task_id, status="completed", result=verification,
        artifact_type="prior_art_verification",
        artifact_payload={
            "memory_key": "kenji/sprint10_concept_verification",
            "queries_run": sum(len(v) for v in retrieval.values()),
            "results_retrieved": total,
        },
    )

    print(f"[{NAME}]\n\n{verification}")
    print(f"\n\n--- {len(verification)} chars ---")


if __name__ == "__main__":
    run()
