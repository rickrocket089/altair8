"""Scope how much of the literature we actually need sits behind a paywall.

Not a prior-art verdict -- that is Kenji's job and needs a brief. This only
answers the founder's question: which specific sources, and is it a short list
or a field.

Each query maps to an open question in the record. Results are reported with
venue and open-access status, so the answer to "do we need ACM access" is a
number rather than an assumption.
"""
from tools import papers

QUERIES = [
    ("C1 prior art -- argument mapping interfaces",
     "argument mapping software interface deliberation support"),
    ("C1 prior art -- confidence/uncertainty encoding",
     "uncertainty visualization confidence encoding visual representation"),
    ("Form-to-task formal systems",
     "automating design graphical presentations expressiveness effectiveness criteria"),
    ("Task taxonomies for visualization",
     "multi-level typology abstract visualization tasks taxonomy"),
    ("Audience/personalisation in visualization",
     "personalized visualization audience characteristics tailoring comprehension"),
    ("Backlog #18 -- C2 prior art (persona/audience agents)",
     "persona simulation audience feedback design tool"),
    ("Backlog #18 -- C6 prior art (embedded/diegetic data)",
     "embedded data representation situated visualization in context"),
    ("Narrative structure / reader-paced storytelling",
     "narrative visualization storytelling reader driven structure"),
]

total = oa = 0
rows = []
for label, q in QUERIES:
    try:
        res = papers.search_openalex(q, max_results=5, year_from=1984)
    except Exception as exc:
        print(f"\n### {label}\n   FAILED: {type(exc).__name__}: {str(exc)[:80]}")
        continue
    print(f"\n### {label}")
    for p in res:
        total += 1
        free = p["is_oa"]
        oa += 1 if free else 0
        mark = "FREE" if free else "PAY "
        venue = (p["venue"] or "?")[:38]
        print(f"  [{mark}] {p['year']} | {venue:38} | {p['title'][:62]}")
        rows.append((free, p["venue"] or "", p["title"]))

print(f"\n=== {oa}/{total} open access ({round(100*oa/max(total,1))}%) ===")
closed_venues = {}
for free, venue, _ in rows:
    if not free:
        closed_venues[venue] = closed_venues.get(venue, 0) + 1
print("paywalled by venue:")
for v, n in sorted(closed_venues.items(), key=lambda x: -x[1]):
    print(f"  {n:2}  {v or '(unknown)'}")
