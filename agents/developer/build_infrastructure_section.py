"""Entry point for Mateo to build a new "Our Infrastructure" website section
visualizing Altair8's actual technical stack -- containers, data stores, LLM
connections, literature databases, and web publishing -- for researchers who
want to understand not just the process (Methodology section) but the
substrate it runs on.
"""
import os
import re

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.developer.persona import NAME, SYSTEM_PROMPT
from agents.permissions import require_tool
from tools import db

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

SITE_HTML = os.path.join(
    os.path.dirname(__file__), "..", "..", "workspace", "outputs", "site-concept-1-editorial.html"
)

EXISTING_TOKENS = """
:root {
    --cream:     #ffffff;
    --cream-dark:#eef0ee;
    --ink:       #14181a;
    --ink-mid:   #3c4547;
    --ink-light: #6d7679;
    --rule:      #dadfde;
    --accent:    #20795b;   /* forest green -- primary accent */
    --accent-lt: #409679;
    --accent2:   #a16a17;   /* ochre -- complementary accent, used for "needs attention" / secondary states */
    --accent2-lt:#d19a47;
    --max:       740px;
    --wide:      960px;
}
body font: 'Iowan Old Style', 'Palatino Linotype', Palatino, Georgia, serif.
Existing patterns to reuse rather than reinvent: .container / .container--wide,
.section-label (small uppercase eyebrow in --accent), .flow-node / .flow-connector
/ .parallel-block (the boxes-and-arrows diagram language already established in
the Methodology section's sprint-cycle diagram -- reuse this same visual
vocabulary for an architecture diagram, don't invent a new diagram style),
.checklist-table (bordered data table pattern), the two-star logo mark
(diagonal green + ochre stars, already used in the nav/favicon).
"""

INFRASTRUCTURE_GROUND_TRUTH = """
REAL INFRASTRUCTURE, VERIFIED BY READING THE ACTUAL REPO (not invented):

LOCAL COMPUTE (everything currently runs on localhost, no cloud deployment yet):
4 Docker containers via docker-compose, on one shared network:
- "agents" container: built from python:3.11-slim, no persistent process --
  each agent run is `docker compose run --rm agents python -m agents.<folder>[.<script>]`,
  a fresh container per invocation.
- "db": postgres:16 -- the relational source of truth.
- "chromadb": chromadb/chroma:latest -- vector memory.
- "dashboard": Flask app, port 5050 -- the internal ops view (KPIs, curated
  findings, sprint timeline, team roster, open tasks). NOT the same as the
  public website (which is a separate static HTML file pushed via FTPS).

POSTGRES TABLES (the relational source of truth):
- agent_memory: key-value store per agent (status, last outputs, north_star, etc.)
- tasks: every unit of work, now with artifact_type + artifact_payload JSONB
  (typed handoffs between agents, adopted from AI-Scientist-v2 in Sprint 3)
- papers: literature search results, now with source + external_id columns
  (arxiv / semantic_scholar / openalex / ieee_xplore, added Sprint 5 prep)
- token_usage: per-agent input/output token logging for cost tracking
- sprints: sprint_number, question, outcome, status -- the sprint timeline
- reviews: reviewer sign-offs (approved / rejected / needs_revision) -- a
  sprint literally cannot close in the database unless the latest review
  for it is 'approved'. This is a real enforced gate, not a convention.

CHROMADB (vector memory, semantic search over past work):
4 collections, one per agent role: researcher_memory (shared by both
researchers -- Kenji and Naledi), developer_memory (Mateo), reviewer_memory
(Ingrid), team_leader_memory (Sophie). Uses the all-MiniLM-L6-v2 embedding
model (downloaded into the container on first run).

LLM CONNECTIVITY:
- ANTHROPIC_API_KEY -> Claude Sonnet 4.6 powers all 5 agent personas'
  actual reasoning (research briefs, reviews, prototypes, planning).
- OPENAI_API_KEY -> gpt-image-1, used only for one narrow purpose: Mateo's
  team-photo generation tool. Not used for any reasoning.
- Both keys live in plain config/.env (gitignored, never committed).

RESEARCH LITERATURE DATABASES (tools/papers.py):
- arXiv: free, no key, preprints.
- Semantic Scholar: free API, works without a key but rate-limited on the
  shared public pool -- a free key raises the limit.
- OpenAlex: free, fully open, no key required, broadest coverage.
- IEEE Xplore: requires a free registered developer key (metadata/abstract
  only, no full-text access even with a key -- full text requires a
  separate institutional subscription). Added specifically because arXiv
  alone missed IEEE VIS, the leading visualization research venue.
All four are queried together via a single search_all_sources() call that
tolerates individual source failures rather than failing the whole search.

WEB PUBLISHING (this website):
- Explicit FTPS (TLS) to an external host, running the publish script
  directly on the founder's Windows machine (not inside Docker) because it
  shells out to a local `sops` binary.
- Credentials are encrypted at rest with sops + age (not plain .env) --
  deliberately a stricter standard than the LLM API keys, because this
  credential grants write access to public-facing infrastructure, not just
  API billing.

VERSION CONTROL:
GitHub repo (rickrocket089/altair8) is the source of truth for all code --
agents, tools, schema, the website source files.

AGENT SAFETY LAYER:
agents/permissions.py -- each agent has an explicit, constrained list of
actions it's allowed to take (adopted from AI-Scientist-v2, Sprint 3),
enforced by a require_tool() check at the start of every script, not left
to good behavior.
"""


def build_context() -> str:
    return (
        f"EXISTING DESIGN SYSTEM -- honor it:\n{EXISTING_TOKENS}\n\n"
        f"{INFRASTRUCTURE_GROUND_TRUTH}\n\n"
        f"CURRENT SPRINT STATE (for scale/context, not to feature prominently):\n"
        + "\n".join(
            f"- Sprint {s['sprint_number']} [{s['status']}]"
            for s in db.list_sprints()
        )
    )


def run() -> None:
    require_tool("mateo", "write_prototype_file")
    db.set_memory("mateo", "status", "online")

    context = build_context()

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Build a new website section titled 'Our Infrastructure' "
                    "for altair8labs.tech -- for researchers who want to know "
                    "exactly what Altair8 actually runs on, not marketing "
                    "language about 'cloud-native AI infrastructure.' This is "
                    "the technical companion to the existing Methodology "
                    "section (which explains process; this explains the "
                    "substrate underneath).\n\n"
                    f"{context}\n\n"
                    "Structure it around two groups, made visually distinct: "
                    "(1) LOCAL -- everything running on localhost via Docker "
                    "right now (the 4 containers, Postgres tables, ChromaDB "
                    "collections), and (2) EXTERNAL CONNECTIONS -- everything "
                    "reached over the network (Anthropic API, OpenAI API, the "
                    "4 literature databases, FTPS publishing, GitHub). Be "
                    "honest that this is a single-machine, localhost setup "
                    "right now, not a distributed cloud system -- don't "
                    "inflate it.\n\n"
                    "Apply the dataviz skill's form heuristic: the content's "
                    "job here is showing system topology and grouping (what "
                    "runs where, what talks to what), not a data comparison "
                    "-- so a boxes-and-connectors architecture diagram is the "
                    "right form. Reuse the EXACT visual vocabulary already "
                    "established in the Methodology section's flow diagram "
                    "(.flow-node, .flow-connector, .parallel-block classes "
                    "and their sibling patterns) rather than inventing a new "
                    "diagram style -- this is a deliberate consistency choice, "
                    "the artifact-design skill's 'honor what's already there' "
                    "rule applied to your own prior work, not just the base "
                    "template. You may extend those classes with new "
                    "modifiers if the topology needs something the sprint-"
                    "cycle diagram didn't (e.g. a two-column local/external "
                    "grouping), but the node/connector/color language should "
                    "feel like the same system, not a different diagram "
                    "library. Use --accent for the local/internal group and "
                    "--accent2 for the external-connections group -- a "
                    "meaningful color-coded grouping, not decoration.\n\n"
                    "Include the real Postgres table list and the real "
                    "ChromaDB collection list as actual content (a compact "
                    "list or small table), not vague summaries -- name them. "
                    "Also include one honest paragraph on the security "
                    "posture: why FTP credentials are sops-encrypted while "
                    "LLM API keys are plain .env (risk-based, not "
                    "inconsistent -- one grants write access to public "
                    "infrastructure, the other is read-only API billing).\n\n"
                    "Keep markup lean: define one reusable inline-code class "
                    "(e.g. .infra-code) in the CSS block instead of repeating "
                    "a full inline style= block on every <code> tag -- the "
                    "content is detailed enough without that repetition "
                    "bloating the output.\n\n"
                    "Output ONLY a self-contained HTML fragment: any new CSS "
                    "you need in one <style> block first (reuse existing "
                    "class names where the pattern already fits; only add "
                    "new rules for genuinely new elements), then the "
                    "<section>...</section> markup, in a single ```html "
                    "fenced code block. No explanation before or after."
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    text = response.content[0].text
    db.log_usage("mateo", response.usage.input_tokens, response.usage.output_tokens)

    match = re.search(r"```html\n(.*?)```", text, re.DOTALL)
    fragment = match.group(1).strip() if match else text.strip()

    out_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "workspace", "outputs", "infrastructure-section.html"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(fragment)

    db.set_memory("mateo", "infrastructure_section_html", fragment)
    print(f"[{NAME}] Infrastructure section written to {out_path}")


if __name__ == "__main__":
    run()
