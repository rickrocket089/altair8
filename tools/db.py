"""Postgres helpers shared by all Altair8 agents."""
import os
import psycopg2
from psycopg2.extras import Json, RealDictCursor

from agents.permissions import require_tool


def get_connection():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "db"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=os.environ.get("POSTGRES_DB", "altair8"),
        user=os.environ.get("POSTGRES_USER", "altair"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
    )


def set_memory(agent_name: str, key: str, value: str) -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO agent_memory (agent_name, key, value, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (agent_name, key)
            DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
            """,
            (agent_name, key, value),
        )
        conn.commit()


def get_memory(agent_name: str, key: str) -> str | None:
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT value FROM agent_memory WHERE agent_name = %s AND key = %s",
            (agent_name, key),
        )
        row = cur.fetchone()
        return row["value"] if row else None


def create_task(created_by: str, assigned_to: str, title: str, description: str = "") -> int:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO tasks (assigned_to, created_by, title, description)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (assigned_to, created_by, title, description),
        )
        task_id = cur.fetchone()[0]
        conn.commit()
        return task_id


def update_task(
    task_id: int,
    status: str,
    result: str = "",
    artifact_type: str | None = None,
    artifact_payload: dict | None = None,
) -> None:
    """Mark a task done. If artifact_type/artifact_payload are given, the
    completion is backed by a typed artifact row (adopted from
    AI-Scientist-v2's typed inter-phase handoff) rather than just a status
    flip -- artifact_payload should reference where the full content lives
    (agent_memory key, vectorstore doc id), not duplicate large text blobs.
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE tasks
            SET status = %s, result = %s, artifact_type = %s, artifact_payload = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (status, result, artifact_type, Json(artifact_payload) if artifact_payload else None, task_id),
        )
        conn.commit()


def log_usage(agent_name: str, input_tokens: int, output_tokens: int) -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO token_usage (agent_name, input_tokens, output_tokens)
            VALUES (%s, %s, %s)
            """,
            (agent_name, input_tokens, output_tokens),
        )
        conn.commit()


def total_usage() -> dict:
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT COALESCE(SUM(input_tokens),0) AS input_tokens, "
            "COALESCE(SUM(output_tokens),0) AS output_tokens FROM token_usage"
        )
        return dict(cur.fetchone())


def list_open_tasks() -> list[dict]:
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT id, assigned_to, title, status FROM tasks "
            "WHERE status != 'completed' ORDER BY created_at DESC"
        )
        return [dict(r) for r in cur.fetchall()]


def paper_count() -> int:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM papers")
        return cur.fetchone()[0]


def create_sprint(sprint_number: int, question: str) -> int:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO sprints (sprint_number, question) VALUES (%s, %s) RETURNING id",
            (sprint_number, question),
        )
        sprint_id = cur.fetchone()[0]
        conn.commit()
        return sprint_id


def complete_sprint(sprint_id: int, outcome: str) -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE sprints SET status = 'completed', outcome = %s, completed_at = NOW() WHERE id = %s",
            (outcome, sprint_id),
        )
        conn.commit()


def list_sprints() -> list[dict]:
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT sprint_number, question, outcome, status, started_at, completed_at "
            "FROM sprints ORDER BY sprint_number ASC"
        )
        return [dict(r) for r in cur.fetchall()]


def get_sprint_id(sprint_number: int) -> int | None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM sprints WHERE sprint_number = %s ORDER BY id DESC LIMIT 1",
            (sprint_number,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def create_review(
    reviewer_agent: str,
    result: str,
    sprint_id: int | None = None,
    task_id: int | None = None,
    notes: dict | None = None,
) -> int:
    """Record a reviewer sign-off. `result` is 'approved', 'rejected', or
    'needs_revision'. Adopted from AI-Scientist-v2's non-author review gate:
    downstream progress (see get_latest_review / log_sprint.py) is blocked
    until an 'approved' row exists.
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO reviews (sprint_id, task_id, reviewer_agent, result, notes)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (sprint_id, task_id, reviewer_agent, result, Json(notes) if notes else None),
        )
        review_id = cur.fetchone()[0]
        conn.commit()
        return review_id


def get_latest_review(sprint_id: int) -> dict | None:
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT id, reviewer_agent, result, notes, created_at FROM reviews "
            "WHERE sprint_id = %s ORDER BY created_at DESC LIMIT 1",
            (sprint_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def create_candidate_approach(
    title: str,
    description: str = "",
    category: str = "",
    source_reference: str = "",
    flagged_by: str = "",
    sprint_id: int | None = None,
    priority: str = "medium",
) -> int:
    """Log a promising lead/finding worth revisiting later (paper, pattern,
    tool) so it doesn't get buried in a brief's prose -- a running backlog,
    checked at sprint planning time via list_candidate_approaches().
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO candidate_approaches
                (title, description, category, source_reference, flagged_by, sprint_id, priority)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (title, description, category, source_reference, flagged_by, sprint_id, priority),
        )
        approach_id = cur.fetchone()[0]
        conn.commit()
        return approach_id


def list_candidate_approaches(status: str | None = "open") -> list[dict]:
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        if status:
            cur.execute(
                "SELECT id, title, description, category, source_reference, flagged_by, "
                "sprint_id, priority, status, created_at FROM candidate_approaches "
                "WHERE status = %s ORDER BY priority DESC, created_at DESC",
                (status,),
            )
        else:
            cur.execute(
                "SELECT id, title, description, category, source_reference, flagged_by, "
                "sprint_id, priority, status, created_at FROM candidate_approaches "
                "ORDER BY priority DESC, created_at DESC"
            )
        return [dict(r) for r in cur.fetchall()]


def update_candidate_approach_status(approach_id: int, status: str) -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE candidate_approaches SET status = %s, updated_at = NOW() WHERE id = %s",
            (status, approach_id),
        )
        conn.commit()


def create_process_review(
    covers_sprint_from: int,
    covers_sprint_to: int,
    conducted_by: str,
    findings: str = "",
    actions_taken: str = "",
) -> int:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO process_reviews
                (covers_sprint_from, covers_sprint_to, conducted_by, findings, actions_taken)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (covers_sprint_from, covers_sprint_to, conducted_by, findings, actions_taken),
        )
        review_id = cur.fetchone()[0]
        conn.commit()
        return review_id


def list_process_reviews() -> list[dict]:
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT id, covers_sprint_from, covers_sprint_to, conducted_by, findings, "
            "actions_taken, conducted_at FROM process_reviews ORDER BY conducted_at ASC"
        )
        return [dict(r) for r in cur.fetchall()]


def create_backlog_item(
    title: str,
    description: str = "",
    proposed_by: str = "",
    priority: str = "medium",
) -> int:
    """Add a candidate sprint topic/question to the backlog -- what sprint
    planning draws from, rather than inventing a question fresh each time.

    Restricted to Sophie (team_leader) -- confirmed with founder 2026-07-27.
    `proposed_by` records who originally suggested the idea (founder, an
    agent's finding, etc.), but only Sophie's own action can write it in.
    """
    require_tool("team_leader", "write_backlog")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sprint_backlog (title, description, proposed_by, priority)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (title, description, proposed_by, priority),
        )
        item_id = cur.fetchone()[0]
        conn.commit()
        return item_id


def list_backlog_items(status: str | None = "open") -> list[dict]:
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        if status:
            cur.execute(
                "SELECT id, title, description, proposed_by, priority, status, "
                "resolved_sprint_id, created_at FROM sprint_backlog "
                "WHERE status = %s ORDER BY priority DESC, created_at ASC",
                (status,),
            )
        else:
            cur.execute(
                "SELECT id, title, description, proposed_by, priority, status, "
                "resolved_sprint_id, created_at FROM sprint_backlog "
                "ORDER BY priority DESC, created_at ASC"
            )
        return [dict(r) for r in cur.fetchall()]


def update_backlog_item_status(item_id: int, status: str, resolved_sprint_id: int | None = None) -> None:
    require_tool("team_leader", "write_backlog")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE sprint_backlog SET status = %s, resolved_sprint_id = %s, updated_at = NOW() WHERE id = %s",
            (status, resolved_sprint_id, item_id),
        )
        conn.commit()
