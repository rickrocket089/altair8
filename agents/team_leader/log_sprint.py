"""Admin entrypoint: log/close a sprint on the timeline.

Run at the close of a sprint, once the team's output for that Sprint
Question has been reviewed. Feeds the dashboard's sprint timeline.

Enforces a hard review gate (adopted from AI-Scientist-v2's non-author
review pattern, Sprint 3 follow-up 2026-07-22): a sprint cannot be marked
completed unless an 'approved' row exists in the `reviews` table for it.
Use --force only for a deliberate override (e.g. backfilling history).
"""
import argparse

from agents.permissions import require_tool
from tools import db


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--number", type=int, required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--outcome", required=True)
    parser.add_argument(
        "--force", action="store_true",
        help="Skip the review-gate check (deliberate override, e.g. backfilling history).",
    )
    args = parser.parse_args()

    require_tool("team_leader", "log_sprint")

    sprint_id = db.get_sprint_id(args.number)
    if sprint_id is None:
        sprint_id = db.create_sprint(args.number, args.question)

    if not args.force:
        review = db.get_latest_review(sprint_id)
        if review is None or review["result"] != "approved":
            found = review["result"] if review else "no review found"
            raise RuntimeError(
                f"Sprint {args.number} cannot be closed: latest review status is "
                f"'{found}', not 'approved'. Run the reviewer's script first, or "
                f"pass --force to override deliberately."
            )

    db.complete_sprint(sprint_id, args.outcome)
    print(f"Sprint {args.number} logged as completed.")


if __name__ == "__main__":
    main()
