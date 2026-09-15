"""Kenji re-runs C1's prior-art question against literature he could not reach.

His Sprint 11 gate-1 brief closed with an explicit limitation: much of the
relevant work sits in ACM and IEEE venues the team's sources index poorly, and
he said so rather than pretending the search was complete. That limitation was
honest and it was also, as of 2026-09-15, no longer true.

Two defects were found that day. The IEEE connector had been returning 403
since it was written -- zero IEEE papers among 1017 retrieved, so IEEE VIS,
VAST and TVCG were invisible to every sprint -- and it failed inside a
tolerant wrapper, so nothing ever surfaced it. And the OpenAlex connector was
discarding venue, publication year and the open-access full-text link, which
reached ACM and IEEE all along but returned results indistinguishable from
noise.

The connector now returns venue, year, OA status and a full-text URL, and
filters by venue ISSN. The first filtered query immediately surfaced work
sitting directly on C1's central claim:

  - In Pursuit of Error: A Survey of Uncertainty Visualization (TVCG 2018)
  - Implicit Error, Uncertainty and Confidence in Visualization (TVCG 2021)
  - Error Bars Considered Harmful: Exploring Alternate Encodings (2014)

C1's claim is that visual weight derives from the author's own confidence.
There is an established research literature on encoding uncertainty and
confidence visually, and this team has never read a line of it. C1 was chosen
as the product direction in Sprint 10 with this unverified; Ingrid named that
omission in her audit the same morning.

This is not a sprint. It runs as a founder-commissioned task, the same footing
as the two audits Ingrid ran on 2026-09-15.
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
TVCG_ISSN = "1077-2626"  # IEEE TVCG: InfoVis, VAST and SciVis all publish here


def _fmt(hits: list[dict]) -> str:
    out = []
    for h in hits:
        venue = h.get("venue") or ""
        year = h.get("year") or ""
        oa = "FREE FULL TEXT" if h.get("is_oa") else "abstract only"
        head = f"  - [{h.get('source','?')}] {h.get('title','(untitled)')}"
        meta = f"    {venue} {year} | {oa}" if venue or year else f"    {oa}"
        out.append(f"{head}\n{meta}\n    {(h.get('abstract') or '(no abstract returned)')[:700]}")
    return "\n".join(out)


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    prior = db.get_memory("kenji", "c1_argument_visualization_check") or ""
    spec = db.get_memory("mateo", "c1_spanning_scaffold_spec") or ""

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Re-verify C1 against the uncertainty-visualization literature",
        description="Founder-commissioned. The literature you declared unreachable is now reachable.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    with client.messages.stream(
        model=MODEL, max_tokens=3000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Your Sprint 11 prior-art brief ended with a limitation you stated "
            "yourself: much of the relevant work is in ACM and IEEE venues our "
            "sources index poorly, and this search was what could be done "
            "meanwhile, not a substitute for reaching them. That was the right "
            "thing to write. It is now out of date.\n\n"
            "Two connector defects were found on 2026-09-15. IEEE Xplore had "
            "been returning 403 since it was written -- zero IEEE papers out of "
            "1017 ever retrieved, inside a wrapper that tolerates failures, so "
            "it never surfaced. And OpenAlex, which does index ACM and IEEE, "
            "was throwing away venue, year and the open-access full-text link "
            "before you ever saw a result. Both are fixed. A first filtered "
            "query surfaced, in IEEE TVCG alone:\n"
            "  - In Pursuit of Error: A Survey of Uncertainty Visualization (2018)\n"
            "  - Implicit Error, Uncertainty and Confidence in Visualization (2021)\n"
            "  - Error Bars Considered Harmful: Exploring Alternate Encodings (2014)\n\n"
            "C1 claims that visual weight derives from the author's own "
            "confidence. There is an entire research tradition on encoding "
            "uncertainty and confidence visually and we have read none of it. "
            "C1 became the product direction with this unverified.\n\n"
            "Design 10 queries. Aim them at two things and keep them "
            "separable:\n\n"
            "A. UNCERTAINTY AND CONFIDENCE ENCODING (7 queries). The question "
            "is not whether uncertainty visualization exists -- it plainly "
            "does. It is whether any of it does what C1 claims as its own: "
            "visual weight (size, opacity, prominence) derived from a "
            "confidence value that is attached to an EPISTEMIC CATEGORY the "
            "author assigned to their own claim -- evidence, inference, "
            "assumption, assertion -- rather than from statistical uncertainty "
            "in data. That distinction is the whole of C1's defensible "
            "position. Design queries that could find the thing that kills it, "
            "not queries that confirm it is safe.\n\n"
            "B. THE FORMAL FORM-TO-TASK TRADITION (3 queries). Mackinlay's APT "
            "(ACM TOG 1986) already falsified concept C3's novelty claim in "
            "Sprint 10, and Casner's task-analytic follow-up (1991) is "
            "reachable too. This tradition formalises which encoding suits "
            "which data job. Hypothesis 2 of this programme -- that visual "
            "form should derive from audience and goal rather than content "
            "type alone -- needs to know how much of it that tradition already "
            "settled, and where it stops. Specifically: does any of it model "
            "the AUDIENCE, or only the data and the task?\n\n"
            f"YOUR OWN PRIOR BRIEF, for what you already covered:\n{prior}\n\n"
            'Return ONLY a JSON array of 10 query strings. No prose, no fences.'
        )}],
    ) as stream:
        qresp = stream.get_final_message()
    db.log_usage("kenji", qresp.usage.input_tokens, qresp.usage.output_tokens)

    raw = re.sub(r"^```(?:json)?|```$", "", qresp.content[0].text.strip(), flags=re.M).strip()
    queries = json.loads(raw)
    print(f"[{NAME}] {len(queries)} queries designed.")

    retrieval = []
    for q in queries:
        hits = []
        try:
            hits += papers.search_all_sources(q, max_results_per_source=6)
        except Exception as exc:
            print(f"[{NAME}]   all-sources failed '{q[:44]}': {exc}")
        try:
            # Venue-scoped pass: TVCG is where InfoVis/VAST publish, and is
            # exactly what was invisible until today.
            hits += papers.search_openalex(q, max_results=6, venue_issn=TVCG_ISSN)
        except Exception as exc:
            print(f"[{NAME}]   tvcg pass failed '{q[:44]}': {exc}")
        seen, deduped = set(), []
        for h in hits:
            key = (h.get("title") or "").lower()[:90]
            if key and key not in seen:
                seen.add(key)
                deduped.append(h)
        retrieval.append({"query": q, "hits": deduped})
        oa_n = sum(1 for h in deduped if h.get("is_oa"))
        print(f"[{NAME}]   '{q[:58]}' -> {len(deduped)} ({oa_n} free)")
        time.sleep(2)

    evidence = "\n\n".join(
        f"QUERY: {r['query']}  ({len(r['hits'])} results)\n{_fmt(r['hits'])}"
        for r in retrieval
    )

    with client.messages.stream(
        model=MODEL, max_tokens=16000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Your queries have been run, including a venue-scoped pass over "
            "IEEE TVCG that was impossible before today. Results below carry "
            "venue, year and whether a free full text exists.\n\n"
            "Ground rules, unchanged: verify against retrieved evidence, label "
            "recollection as recollection, and never describe a check you did "
            "not perform. One addition specific to today -- most of what you "
            "have below is an ABSTRACT, not a full text. Where a verdict needs "
            "the mechanism and the mechanism lives in the body of the paper, "
            "say that the verdict is provisional and name the paper that has "
            "to be read in full. Do not let an abstract stand in for a "
            "mechanism.\n\n"
            "PRODUCE:\n\n"
            "1. RETRIEVAL LOG. Queries, returned, retained, noise rate, and "
            "how much of what you retained is free full text versus abstract "
            "only.\n\n"
            "2. THE QUESTION THAT DECIDES C1. Does any retrieved work derive "
            "visual weight from a confidence value attached to an epistemic "
            "category the author assigned to their own claim -- as opposed to "
            "statistical uncertainty in data? Yes or no, with citations. If "
            "the honest answer is 'the distinction may not survive contact "
            "with this literature', say that.\n\n"
            "3. WHAT C1 CAN STILL CLAIM. Restate its defensible position as "
            "narrowly as the evidence now allows. It has already narrowed once, "
            "in Sprint 10. Narrow it again if it must, and if it narrows to "
            "nothing, say so plainly -- the founder is making a direction "
            "decision on this and a comfortable answer is worth less than "
            "nothing.\n\n"
            "4. THE FORMAL TRADITION AND HYPOTHESIS 2. How much of "
            "form-to-task selection did Mackinlay, Casner and that line already "
            "formalise, and where does it stop? The specific question: does "
            "any of it model the AUDIENCE, or only data and task? This "
            "programme's central claim is that audience and goal should drive "
            "form. If that tradition already did it, our gap claim narrows; if "
            "it deliberately did not, say what it treated as out of scope and "
            "why.\n\n"
            "5. DOES YOUR SPRINT 11 VERDICT CHANGE? You cleared C1's novelty "
            "position conditionally, with the unreached-literature caveat "
            "attached. With part of that literature now in hand, does the "
            "verdict hold, narrow, or fall?\n\n"
            "6. WHAT IS STILL UNREACHED. Be specific: CHI and UIST are "
            "conference series without an ISSN and cannot yet be venue-"
            "filtered, so name what you would still want and where it lives, "
            "rather than restating that a gap exists.\n\n"
            f"C1'S SCAFFOLD SPEC, for what the mechanism actually is:\n{spec[:12000]}\n\n"
            f"YOUR SPRINT 11 BRIEF:\n{prior}\n\n"
            f"RETRIEVED EVIDENCE:\n{evidence}\n"
        )}],
    ) as stream:
        resp = stream.get_final_message()

    brief = resp.content[0].text
    db.log_usage("kenji", resp.usage.input_tokens, resp.usage.output_tokens)

    db.set_memory("kenji", "c1_uncertainty_literature_check", brief)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"brief-task-{task_id}",
        text=brief,
        metadata={"agent": "kenji", "type": "c1_uncertainty_literature_check"},
    )
    db.update_task(
        task_id, status="completed", result=brief,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/c1_uncertainty_literature_check"},
    )

    for r in retrieval:
        for h in r["hits"]:
            try:
                papers.save_paper(h)
            except Exception:
                pass

    print(f"[{NAME}]\n\n{brief}")
    print(f"\n\n--- {len(brief)} chars, stored as kenji/c1_uncertainty_literature_check ---")


if __name__ == "__main__":
    run()
