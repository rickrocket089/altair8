"""Kenji builds a concrete manual-download acquisition list for the founder.

Backlog #15 (ACM DL / CHI / UIST / InfoVis access) was diagnosed 2026-09-15 as
mostly a connector defect, not a paywall problem -- 39/40 scoped results were
open access, just served by dl.acm.org with a 403 to non-browser clients. The
founder can download in a real browser what no script can fetch. He asked
Sophie one question in a live chat on 2026-09-16: not "give me a literature
review," but "tell me exactly which papers you need."

This produces a short, named list -- not a survey -- scoped to what three
still-open items actually need:
  (a) C1's residual novelty risk: argument-mapping tools (Rationale,
      Compendium) that Priya flagged as an unchecked risk and that were never
      searched.
  (b) Backlog #18's two least-reached gaps: NLG audience/user-model planning
      (Paris, Moore, Reiter & Dale) for C2, and Brown & Levinson politeness
      theory in dialogue systems for C5. (C6's gap -- game studies / design
      history / data-journalism practice -- is largely non-ACM/CHI and is
      intentionally left out of this ACM-focused pass.)
  (c) Candidate #11's own "check first, cheaper" step: whether the formal
      form-to-task tradition (Munzner's task taxonomy, grammar-of-graphics
      work) already models AUDIENCE, before any corpus/knowledge-graph gets
      built to supply that.

Named-target title queries are used wherever a specific work is already
suspected (the lesson from the APT/Casner miss on 2026-09-15: conceptual
queries can miss canonical prior art that a literal title search finds in
minutes), alongside conceptual queries for the less-targeted gaps.
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


def _fmt(hits: list[dict]) -> str:
    out = []
    for h in hits:
        venue = h.get("venue") or ""
        year = h.get("year") or ""
        oa = "FREE FULL TEXT" if h.get("is_oa") else "abstract only / access unclear"
        head = f"  - [{h.get('source','?')}] {h.get('title','(untitled)')}"
        meta = f"    {venue} {year} | {oa} | url: {h.get('url') or h.get('pdf_url') or '(none)'}"
        out.append(f"{head}\n{meta}\n    {(h.get('abstract') or '(no abstract returned)')[:500]}")
    return "\n".join(out)


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Build a concrete ACM/CHI/UIST manual-acquisition list",
        description=(
            "Founder-commissioned, live chat 2026-09-16. He will download PDFs "
            "manually and asked for named papers, not a literature review."
        ),
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    with client.messages.stream(
        model=MODEL, max_tokens=2200, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "The founder cannot reach ACM DL programmatically but can download "
            "papers manually in a browser -- dl.acm.org 403s scripted clients "
            "but not people, and backlog #15's diagnosis on 2026-09-15 found "
            "39 of 40 scoped results were open access anyway. He asked Sophie "
            "one direct question: not a literature review, but which specific "
            "papers we actually need. You are answering it.\n\n"
            "Design up to 14 queries across three named gaps. Use literal "
            "title-phrase queries for anything you can already name -- the "
            "lesson from missing Mackinlay/Casner on a conceptual query this "
            "same week -- and conceptual queries only where nothing specific "
            "is already suspected.\n\n"
            "GAP A -- C1's unchecked risk (4-5 queries). Priya flagged "
            "argument-mapping / rationale-visualization tools as an unchecked "
            "risk to C1's novelty and nobody has searched for them. Query by "
            "name: Rationale (van Gelder), Compendium (Buckingham Shum / "
            "Selvin), and the broader IBIS / Toulmin-diagram computer-"
            "supported-argumentation tradition. The question each query "
            "serves: does any of these derive visual weight/prominence from "
            "an author-assigned epistemic confidence, the same mechanism C1 "
            "claims? If yes, C1's novelty narrows further; if these tools "
            "structure argument but never weight it by confidence, that's a "
            "real, citable distinction.\n\n"
            "GAP B -- backlog #18's two least-reached literatures (6 "
            "queries, 3 each). C2 needs the NLG audience/user-model planning "
            "line: query by name -- Paris (user-model-based text generation), "
            "Moore & Paris (planning text for advisory dialogues), Reiter & "
            "Dale (building NLG systems). C5 needs Brown & Levinson politeness "
            "theory as implemented in computational/dialogue systems -- query "
            "both the original theory's computational uptake and specifically "
            "'politeness' + 'dialogue system' or 'NLG'.\n\n"
            "GAP C -- candidate #11's cheaper-first check (3-4 queries). "
            "Before any corpus/knowledge-graph gets built to teach form "
            "selection, check whether the formal tradition already models "
            "AUDIENCE, not just data and task. Query Munzner's task taxonomy "
            "for visualization, grammar-of-graphics work (Wilkinson), and any "
            "extension of Mackinlay/Casner-style expressiveness/effectiveness "
            "criteria that explicitly includes an audience or reader model.\n\n"
            "Return ONLY a JSON array of query strings, each tagged by gap. "
            "Format: [{\"gap\": \"A\", \"query\": \"...\"}, ...]. No prose, no fences."
        )}],
    ) as stream:
        qresp = stream.get_final_message()
    db.log_usage("kenji", qresp.usage.input_tokens, qresp.usage.output_tokens)

    raw = re.sub(r"^```(?:json)?|```$", "", qresp.content[0].text.strip(), flags=re.M).strip()
    queries = json.loads(raw)
    print(f"[{NAME}] {len(queries)} queries designed.")

    retrieval = []
    for item in queries:
        q, gap = item["query"], item.get("gap", "?")
        hits = []
        try:
            hits += papers.search_all_sources(q, max_results_per_source=6)
        except Exception as exc:
            print(f"[{NAME}]   ({gap}) failed '{q[:44]}': {exc}")
        seen, deduped = set(), []
        for h in hits:
            key = (h.get("title") or "").lower()[:90]
            if key and key not in seen:
                seen.add(key)
                deduped.append(h)
        retrieval.append({"gap": gap, "query": q, "hits": deduped})
        oa_n = sum(1 for h in deduped if h.get("is_oa"))
        print(f"[{NAME}]   ({gap}) '{q[:52]}' -> {len(deduped)} ({oa_n} free)")
        time.sleep(2)

    evidence = "\n\n".join(
        f"GAP {r['gap']} | QUERY: {r['query']}  ({len(r['hits'])} results)\n{_fmt(r['hits'])}"
        for r in retrieval
    )

    with client.messages.stream(
        model=MODEL, max_tokens=4000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Produce the founder's acquisition list from the retrieval below. "
            "Ground rules: this is a shopping list, not a brief -- rank by "
            "what actually closes an open question, drop anything tangential "
            "even if it looks relevant, and cap it at what a person would "
            "actually go download (aim for 6-10 papers total, not one per "
            "query). For each paper give: title, authors, year, venue, "
            "whether it showed as free full text or needs the founder to "
            "fetch it manually from dl.acm.org (or wherever it lives), the "
            "URL/DOI if you have one, and ONE sentence on which open question "
            "it closes and how. Group by gap (A/B/C). If a gap's queries "
            "returned nothing usable, say so plainly rather than padding it "
            "with a marginal result -- an honest 'nothing found, here's the "
            "next query to try' is worth more than a weak citation.\n\n"
            "End with a short paragraph: of these, which ONE paper would you "
            "read first if the founder only downloads one today, and why.\n\n"
            f"RETRIEVED EVIDENCE:\n{evidence}\n"
        )}],
    ) as stream:
        resp = stream.get_final_message()

    brief = resp.content[0].text
    db.log_usage("kenji", resp.usage.input_tokens, resp.usage.output_tokens)

    db.set_memory("kenji", "acm_acquisition_list", brief)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"brief-task-{task_id}",
        text=brief,
        metadata={"agent": "kenji", "type": "acm_acquisition_list"},
    )
    db.update_task(
        task_id, status="completed", result=brief,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/acm_acquisition_list"},
    )

    for r in retrieval:
        for h in r["hits"]:
            try:
                papers.save_paper(h)
            except Exception:
                pass

    print(f"[{NAME}]\n\n{brief}")
    print(f"\n\n--- {len(brief)} chars, stored as kenji/acm_acquisition_list ---")


if __name__ == "__main__":
    run()
