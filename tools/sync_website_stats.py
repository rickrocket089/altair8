"""Patch the website's live-derived stat counters from the real database
state, in place, before publish_website.py runs.

Third time this drifted in one session (2026-09-16): "10" -> "16" (2026-07-27,
founder caught it), "270" corrected mid-session, then caught stale again an
hour later at 1,252 vs. a real count of 1,381 after one more research task.
The site is static HTML, hand-edited per sprint close -- nothing regenerates
these numbers automatically, so every session that runs extra literature
searches after the last manual edit leaves the stat silently wrong again.

This does not make the site a live template (still static HTML, same as
always) -- it patches exactly the stat-number spans that are meant to track
live counts, run as an explicit step, not a background job. Sprint count
still comes from Sophie's own sprint-closing edit (it needs the sprint's
narrative content anyway, which this script doesn't generate) -- only the
paper counter, which drifts silently because nothing about it requires a
narrative edit, is synced here.

Usage (inside the agents container, needs DB access):
    docker compose run --rm agents python -m tools.sync_website_stats
Then run tools/publish_website.py on the host as usual.
"""
import os
import re

from tools import db

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_HTML = os.path.join(REPO_ROOT, "workspace", "outputs", "site-concept-1-editorial.html")

STAT_BLOCK_RE = re.compile(
    r'(<span class="stat-number">)([\d,]+)(</span>\s*'
    r'<span class="stat-label">Science papers screened</span>)'
)


def run() -> None:
    count = db.paper_count()
    formatted = f"{count:,}"

    with open(SITE_HTML, encoding="utf-8") as f:
        html = f.read()

    matches = STAT_BLOCK_RE.findall(html)
    if not matches:
        raise RuntimeError(
            "No 'Science papers screened' stat block found -- site markup "
            "may have changed; update STAT_BLOCK_RE."
        )

    before = [m[1] for m in matches]
    html = STAT_BLOCK_RE.sub(lambda m: f"{m.group(1)}{formatted}{m.group(3)}", html)

    with open(SITE_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    if all(b == formatted for b in before):
        print(f"Already in sync: {formatted} (no change).")
    else:
        print(f"Synced {len(matches)} stat block(s): {set(before)} -> {formatted}")


if __name__ == "__main__":
    run()
