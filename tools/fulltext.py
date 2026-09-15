"""Fetch, extract and index the full text of a paper.

The project retrieved 1098 papers before this existed and stored not one full
text. Every novelty verdict to date rests on titles and abstracts, and Kenji
has twice had to mark a verdict provisional because the mechanism he needed to
compare lives in a paper's body rather than its summary. `pypdf` had been sitting
in requirements.txt since July, unused, and workspace/papers/ was empty apart
from its .gitkeep.

What this does: downloads a PDF, extracts its text, keeps both on disk, and
indexes the text in chunks into a Chroma collection so any agent can retrieve
passages by meaning rather than re-reading the whole paper into a prompt.

Deliberately not automatic over the whole corpus. Full texts are large, many
are paywalled, and indexing everything retrieved would bury the few papers that
actually decide something. One paper is ingested when a verdict depends on it.
"""
import os
import re

import requests
from pypdf import PdfReader

from tools import vectorstore

PAPERS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspace", "papers"
)
COLLECTION = "paper_fulltext"
CHUNK_CHARS = 1800
CHUNK_OVERLAP = 200


def _slugify(text: str, max_len: int = 60) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-")


def _chunk(text: str) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        end = start + CHUNK_CHARS
        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP
    return chunks


def fetch_pdf(url: str, slug: str) -> str:
    """Download to workspace/papers/<slug>.pdf and return the path."""
    os.makedirs(PAPERS_DIR, exist_ok=True)
    path = os.path.join(PAPERS_DIR, f"{slug}.pdf")
    resp = requests.get(url, timeout=120, headers={"User-Agent": "Altair8-research/1.0"})
    resp.raise_for_status()
    head = resp.content[:5]
    if head[:4] != b"%PDF":
        raise ValueError(
            f"response from {url[:70]} is not a PDF (starts with {head!r}) -- "
            "a login wall or an HTML landing page will look like success otherwise"
        )
    with open(path, "wb") as f:
        f.write(resp.content)
    return path


def extract_text(pdf_path: str) -> tuple[str, int]:
    """Return (text, page_count). Layout is not preserved; this is for reading
    and retrieval, not for reproducing the document."""
    reader = PdfReader(pdf_path)
    pages = [(p.extract_text() or "") for p in reader.pages]
    text = "\n\n".join(pages)
    # Kill the hyphenation that line-wrapping leaves behind, or search for
    # "uncertainty" misses "uncer-\ntainty".
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    return text, len(pages)


def ingest(url: str, title: str, note: str = "") -> dict:
    """Fetch, extract, store and index one paper. Returns a small report."""
    slug = _slugify(title)
    pdf_path = fetch_pdf(url, slug)
    text, pages = extract_text(pdf_path)

    txt_path = os.path.join(PAPERS_DIR, f"{slug}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    chunks = _chunk(text)
    for i, chunk in enumerate(chunks):
        vectorstore.remember(
            collection_name=COLLECTION,
            doc_id=f"{slug}-{i:04d}",
            text=chunk,
            metadata={"slug": slug, "title": title, "chunk": i, "source_url": url,
                      "note": note},
        )

    return {
        "slug": slug, "pdf": pdf_path, "txt": txt_path,
        "pages": pages, "chars": len(text), "chunks": len(chunks),
    }


def ingest_local(pdf_path: str, title: str, note: str = "") -> dict:
    """Same as ingest(), for a PDF already on disk.

    Publishers block automated downloads -- dl.acm.org returns 403 to anything
    that is not a browser, open access or not. Rather than dress this client up
    as a browser to get around that, the founder saves the file and it is
    ingested from disk. Put founder-supplied PDFs in workspace/workfiles/.
    """
    slug = _slugify(title)
    text, pages = extract_text(pdf_path)

    os.makedirs(PAPERS_DIR, exist_ok=True)
    kept_pdf = os.path.join(PAPERS_DIR, f"{slug}.pdf")
    if os.path.abspath(pdf_path) != os.path.abspath(kept_pdf):
        with open(pdf_path, "rb") as src, open(kept_pdf, "wb") as dst:
            dst.write(src.read())

    txt_path = os.path.join(PAPERS_DIR, f"{slug}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    chunks = _chunk(text)
    for i, chunk in enumerate(chunks):
        vectorstore.remember(
            collection_name=COLLECTION,
            doc_id=f"{slug}-{i:04d}",
            text=chunk,
            metadata={"slug": slug, "title": title, "chunk": i,
                      "source_url": "(local file)", "note": note},
        )

    return {"slug": slug, "pdf": kept_pdf, "txt": txt_path,
            "pages": pages, "chars": len(text), "chunks": len(chunks)}


def read(slug: str) -> str:
    """The stored plain text of an ingested paper."""
    with open(os.path.join(PAPERS_DIR, f"{slug}.txt"), encoding="utf-8") as f:
        return f.read()


def search(query: str, n_results: int = 5):
    """Passages across all ingested full texts, by meaning."""
    return vectorstore.recall(COLLECTION, query, n_results=n_results)
