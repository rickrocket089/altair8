"""Research-literature search + storage helpers shared by all Altair8
researchers. Sources: arXiv (legacy), Semantic Scholar, OpenAlex, and IEEE
Xplore -- added 2026-07-23 per founder request, since arXiv alone was the
only literature database in reach (preprints only, no IEEE VIS / CHI-venue
peer-reviewed coverage).
"""
import os

import arxiv
import requests

from tools import db


def search_arxiv(query: str, max_results: int = 5) -> list[dict]:
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    results = []
    for r in client.results(search):
        arxiv_id = r.get_short_id()
        results.append(
            {
                "source": "arxiv",
                "external_id": arxiv_id,
                "arxiv_id": arxiv_id,
                "title": r.title,
                "authors": ", ".join(a.name for a in r.authors),
                "abstract": r.summary,
                "url": r.entry_id,
            }
        )
    return results


def search_semantic_scholar(query: str, max_results: int = 5) -> list[dict]:
    """Free API, no key required for moderate volume. Optional
    SEMANTIC_SCHOLAR_API_KEY in config/.env raises the rate limit.
    """
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": max_results,
        "fields": "title,abstract,authors,year,url,externalIds",
    }
    headers = {}
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key

    resp = requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for paper in data.get("data", []):
        results.append(
            {
                "source": "semantic_scholar",
                "external_id": paper.get("paperId"),
                "title": paper.get("title") or "",
                "authors": ", ".join(a.get("name", "") for a in paper.get("authors", [])),
                "abstract": paper.get("abstract") or "",
                "url": paper.get("url") or "",
            }
        )
    return results


def _reconstruct_openalex_abstract(inverted_index: dict | None) -> str:
    """OpenAlex ships abstracts as {word: [positions]} to dodge copyright
    concerns on full-text reproduction -- reconstruct plain text from it.
    """
    if not inverted_index:
        return ""
    positions: dict[int, str] = {}
    for word, idxs in inverted_index.items():
        for i in idxs:
            positions[i] = word
    return " ".join(positions[i] for i in sorted(positions))


def search_openalex(query: str, max_results: int = 5) -> list[dict]:
    """Free, fully open API, no key required. Set OPENALEX_MAILTO in
    config/.env to join the "polite pool" for higher/more reliable rate limits.
    """
    url = "https://api.openalex.org/works"
    params = {"search": query, "per-page": max_results}
    mailto = os.environ.get("OPENALEX_MAILTO")
    if mailto:
        params["mailto"] = mailto

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for work in data.get("results", []):
        authors = ", ".join(
            a["author"]["display_name"]
            for a in work.get("authorships", [])
            if a.get("author")
        )
        openalex_id = (work.get("id") or "").rsplit("/", 1)[-1]
        results.append(
            {
                "source": "openalex",
                "external_id": openalex_id,
                "title": work.get("title") or work.get("display_name") or "",
                "authors": authors,
                "abstract": _reconstruct_openalex_abstract(work.get("abstract_inverted_index")),
                "url": work.get("id") or "",
            }
        )
    return results


def search_ieee_xplore(query: str, max_results: int = 5) -> list[dict]:
    """Requires a free IEEE Xplore Developer API key (register at
    https://developer.ieee.org/), set as IEEE_XPLORE_API_KEY in config/.env.
    Free tier is rate-limited (~200 calls/day) -- IEEE VIS and other
    visualization/HCI venues are indexed here, which arXiv does not cover.
    """
    api_key = os.environ.get("IEEE_XPLORE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "IEEE_XPLORE_API_KEY not set in config/.env -- register a free "
            "key at https://developer.ieee.org/ first."
        )

    url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
    params = {"apikey": api_key, "querytext": query, "max_records": max_results}

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for article in data.get("articles", []):
        authors_block = article.get("authors", {})
        author_list = authors_block.get("authors", []) if isinstance(authors_block, dict) else []
        results.append(
            {
                "source": "ieee_xplore",
                "external_id": str(article.get("article_number", "")),
                "title": article.get("title") or "",
                "authors": ", ".join(a.get("full_name", "") for a in author_list),
                "abstract": article.get("abstract") or "",
                "url": article.get("pdf_url") or article.get("html_url") or "",
            }
        )
    return results


def search_all_sources(query: str, max_results_per_source: int = 5) -> list[dict]:
    """Search arXiv, Semantic Scholar, OpenAlex, and IEEE Xplore, tolerating
    individual source failures (e.g. IEEE key not configured yet) rather
    than failing the whole search.
    """
    all_results = []
    for fn in (search_arxiv, search_semantic_scholar, search_openalex, search_ieee_xplore):
        try:
            all_results.extend(fn(query, max_results_per_source))
        except Exception as e:
            print(f"[papers] {fn.__name__} failed, skipping: {e}")
    return all_results


def save_paper(paper: dict) -> None:
    source = paper.get("source", "arxiv")
    external_id = paper.get("external_id") or paper.get("arxiv_id")
    arxiv_id = paper.get("arxiv_id") if source == "arxiv" else None

    with db.get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO papers (arxiv_id, source, external_id, title, authors, abstract, url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source, external_id) DO NOTHING
            """,
            (arxiv_id, source, external_id, paper["title"], paper["authors"], paper["abstract"], paper["url"]),
        )
        conn.commit()
