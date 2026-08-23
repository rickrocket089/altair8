"""Logs the database-backup gap found on 2026-08-23.

Found the same way the 2026-08-01 code gap was found: the founder asked whether
everything was saved before shutting the workstation down. Nothing in the
project checks this, which is the actual problem -- a backup taken once because
someone happened to ask is not a backup strategy.
"""
from agents.permissions import require_tool
from tools import db

TITLE = "Automate the database backup — the research record has no backup strategy"

DESCRIPTION = """Found 2026-08-23 when the founder asked, before shutting the
workstation down, whether everything was saved. The code was: clean tree, synced
with origin. The research record was not backed up at all.

Everything the team has produced lives only in the Postgres Docker volume:
1.25 MB of agent memory across 68 keys (Priya's concepts, Kenji's verification
rounds, Naledi's behavioural briefs, Ingrid's reviews, the Sprint 10 synthesis),
plus the sprints, reviews, backlog, candidate_approaches, 1017 papers and the
process reviews. The repo held every script that generated that output and none
of the output itself.

A one-off dump was taken and committed (backups/altair8-db-2026-08-23.sql). That
closes the instance, not the gap.

THE ACTUAL PROBLEM: nothing checks. This is the third time a "is it saved?"
question from the founder has surfaced a real gap -- 2026-08-01 (the whole
codebase existed only locally while the site claimed GitHub was the source of
truth), the Sprint 8 close that never happened, and now this. The pattern
Process Review #1 and #2 both identified: rules and assumptions exist,
enforcement does not.

WHAT WOULD ACTUALLY FIX IT, in rough order of cost:
  - a make/script target that dumps and commits, so it is one command;
  - that target invoked as part of the sprint-close checklist, which already
    exists as the Standing Obligations Check in Sophie's persona and is the
    natural hook;
  - or a scheduled dump if the workstation is up predictably.

Also worth deciding: whether the dump belongs in git at all long-term. 3.8 MB
per snapshot is fine now; committed weekly for a year it is not. Options are
pruning old dumps, dumping schema-plus-agent_memory only, or moving snapshots
out of the repo entirely.

Note for whoever automates it: scan the dump for secrets before committing.
This one was scanned rather than assumed clean -- the hit was the string
"ANTHROPIC_API_KEY" in the website's own infrastructure copy, not a value, but
that check should be part of the script, not a habit."""


def run() -> None:
    require_tool("team_leader", "write_backlog")
    if TITLE in {i["title"] for i in db.list_backlog_items()}:
        print("= already logged.")
        return
    item_id = db.create_backlog_item(
        title=TITLE, description=DESCRIPTION, proposed_by="team_leader", priority="medium",
    )
    print(f"+ backlog [medium] id={item_id}: {TITLE}")


if __name__ == "__main__":
    run()
