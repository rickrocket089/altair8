"""Backlog #23's own stated prerequisite: check whether its interventions
already exist in the literature before the design is finalized.

Backlog #23 (the hypothesis-6 causal behavioral test) ends with an explicit
instruction: "Kenji should check whether these interventions have already
been run on this question. The team was caught twice in Sprint 10 claiming
novelty that prior art had covered." Founder approved starting here,
2026-09-16 -- Sophie only scopes the full 4-phase sprint once this comes
back clear.

Four things to check, matching #23's four phases: (1) causal/interventional
studies of LLM visual-form-selection reasoning (not just observational
ones -- Sprints 6/7/the Gemini addition were all observational, that gap is
the whole point of #23); (2) pre-registration + blind scoring specifically
applied to LLM visualization-reasoning studies; (3) LLM self-evaluation of
its own rendered visual output (a render-and-inspect loop); (4) any existing
"ground-truth convergence" check -- do models or authorities even agree on
a correct visual form for a given scenario.
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
        oa = "FREE FULL TEXT" if h.get("is_oa") else "abstract only"
        head = f"  - [{h.get('source','?')}] {h.get('title','(untitled)')}"
        meta = f"    {venue} {year} | {oa}"
        out.append(f"{head}\n{meta}\n    {(h.get('abstract') or '(no abstract returned)')[:500]}")
    return "\n".join(out)


def run() -> None:
    require_tool("kenji", "write_brief")
    db.set_memory("kenji", "status", "online")

    backlog_23 = None
    for item in db.list_backlog_items(status="open"):
        if item["id"] == 23:
            backlog_23 = item
            break
    if backlog_23 is None:
        raise RuntimeError("Backlog #23 not found or not open -- check status before running.")

    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="kenji",
        title="Backlog #23 prerequisite: prior-art check on its own interventions",
        description="Founder-approved start, 2026-09-16. Gates whether Sophie scopes the full 4-phase sprint.",
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    with client.messages.stream(
        model=MODEL, max_tokens=2000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Backlog #23 (full text below) proposes a causal, interventional "
            "behavioral test of whether LLM visual-form-selection reasoning "
            "is genuine or post-hoc. Its own text ends with an instruction "
            "to check for prior art first -- Sprint 10 caught this team "
            "claiming novelty twice that prior art had already covered.\n\n"
            "Design up to 12 queries across 4 targets, tagged by target:\n\n"
            "TARGET 1 (5 queries) -- CAUSAL INTERVENTION ON LLM VISUALIZATION "
            "REASONING, not observational. Specifically: ablating audience/"
            "goal context and observing form choice; supplying a FALSE "
            "audience premise and checking whether the model's stated "
            "reasoning adapts to justify an unchanged output (a post-hoc-"
            "rationalization detector); forcing form-commitment before vs. "
            "after reasoning; supplying an explicit decision framework and "
            "measuring whether failure disappears. Query by mechanism, not "
            "just by topic -- 'ablation' and 'intervention' and 'causal' "
            "combined with visualization/chart/form selection and LLM.\n\n"
            "TARGET 2 (3 queries) -- PRE-REGISTRATION and BLIND SCORING "
            "applied specifically to LLM output evaluation (not the general "
            "methodology literature, which is well known to exist -- the "
            "question is whether anyone applied it to THIS kind of study, "
            "LLM visualization/chart-selection reasoning specifically).\n\n"
            "TARGET 3 (2 queries) -- LLM SELF-EVALUATION OF ITS OWN RENDERED "
            "VISUAL OUTPUT, i.e. a model shown an image of what it produced "
            "and asked to judge it as a reader would (a render-and-inspect "
            "loop), specifically for charts/visualizations, not general "
            "vision-language self-critique.\n\n"
            "TARGET 4 (2 queries) -- GROUND-TRUTH CONVERGENCE for visual "
            "form selection: do multiple models, or multiple runs of one "
            "model, or published design authorities, actually agree with "
            "each other on what the 'correct' visual form is for a given "
            "scenario? Has anyone measured inter-model or inter-rater "
            "agreement on chart-type selection as a construct-validity "
            "check before measuring 'correctness'?\n\n"
            "Return ONLY a JSON array: [{\"target\": 1, \"query\": \"...\"}, ...]. "
            "No prose, no fences.\n\n"
            f"=== BACKLOG #23, FULL TEXT ===\n{backlog_23['description']}\n"
        )}],
    ) as stream:
        qresp = stream.get_final_message()
    db.log_usage("kenji", qresp.usage.input_tokens, qresp.usage.output_tokens)

    raw = re.sub(r"^```(?:json)?|```$", "", qresp.content[0].text.strip(), flags=re.M).strip()
    queries = json.loads(raw)
    print(f"[{NAME}] {len(queries)} queries designed.")

    retrieval = []
    for item in queries:
        q, target = item["query"], item.get("target", "?")
        hits = []
        try:
            hits += papers.search_all_sources(q, max_results_per_source=6)
        except Exception as exc:
            print(f"[{NAME}]   (T{target}) failed '{q[:44]}': {exc}")
        seen, deduped = set(), []
        for h in hits:
            key = (h.get("title") or "").lower()[:90]
            if key and key not in seen:
                seen.add(key)
                deduped.append(h)
        retrieval.append({"target": target, "query": q, "hits": deduped})
        oa_n = sum(1 for h in deduped if h.get("is_oa"))
        print(f"[{NAME}]   (T{target}) '{q[:52]}' -> {len(deduped)} ({oa_n} free)")
        time.sleep(2)

    evidence = "\n\n".join(
        f"TARGET {r['target']} | QUERY: {r['query']}  ({len(r['hits'])} results)\n{_fmt(r['hits'])}"
        for r in retrieval
    )

    with client.messages.stream(
        model=MODEL, max_tokens=6000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            "Retrieval is done. Produce the prior-art verdict backlog #23 "
            "requires before Sophie scopes the sprint.\n\n"
            "For EACH of the 4 targets:\n"
            "1. Did anything retrieved actually do what that target "
            "describes, or just something adjacent (e.g. observational "
            "studies of LLM reasoning that LOOK causal but aren't actually "
            "interventional)? Be exact about this distinction -- it's the "
            "one this whole backlog item exists to enforce.\n"
            "2. If something close exists, does it cover chart/visualization "
            "form selection specifically, or a different domain entirely "
            "(e.g. general LLM faithfulness/hallucination causal studies "
            "that never touch visualization)?\n"
            "3. Verdict: CLEAR (nothing blocks the design as specified), "
            "OVERLAPS (something exists that #23's design should account "
            "for or differentiate from -- name it and say how), or BLOCKED "
            "(this has essentially already been done, name what and where).\n\n"
            "Then an OVERALL VERDICT: is Sophie clear to scope the full "
            "4-phase sprint as designed, or does anything found require the "
            "design to change first? Be direct -- the founder is waiting on "
            "this to decide whether to proceed.\n\n"
            f"=== BACKLOG #23 FULL TEXT ===\n{backlog_23['description']}\n\n"
            f"=== RETRIEVED EVIDENCE ===\n{evidence}\n"
        )}],
    ) as stream:
        resp = stream.get_final_message()

    verdict = resp.content[0].text
    db.log_usage("kenji", resp.usage.input_tokens, resp.usage.output_tokens)

    db.set_memory("kenji", "backlog23_prior_art_check", verdict)
    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"brief-task-{task_id}",
        text=verdict,
        metadata={"agent": "kenji", "type": "backlog23_prior_art_check"},
    )
    db.update_task(
        task_id, status="completed", result=verdict,
        artifact_type="brief",
        artifact_payload={"memory_key": "kenji/backlog23_prior_art_check"},
    )

    for r in retrieval:
        for h in r["hits"]:
            try:
                papers.save_paper(h)
            except Exception:
                pass

    print(f"[{NAME}]\n\n{verdict}")
    print(f"\n\n--- {len(verdict)} chars, stored as kenji/backlog23_prior_art_check ---")


if __name__ == "__main__":
    run()
