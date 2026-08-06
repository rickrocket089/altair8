"""Per-agent action permissions.

Adopted from AI-Scientist-v2 (SakanaAI): https://github.com/SakanaAI/AI-Scientist-v2
-- an agent there is never a general-purpose actor, it has a small, explicit
list of legal actions for its role, enforced by the executor rather than
left to good behavior. This caps the blast radius of a hallucinating agent.
Adopted into Altair8 2026-07-22 (Sprint 3 follow-up), per Mateo's framework-
pattern review and Ingrid's confirmation that this pattern should ship first.

These lists are Altair8's own design choice, not a finding from the
AI-Scientist-v2 source -- only the *pattern* (constrained per-role action
space, enforced at the executor) is borrowed.
"""

PERMITTED_TOOLS = {
    "team_leader": {
        "advance_sprint_phase", "route_task", "read_all",
        "set_north_star", "set_design_principles", "log_sprint", "write_backlog",
    },
    "kenji": {"search_vectorstore", "write_brief", "web_search"},
    "naledi": {"read_brief", "search_vectorstore", "write_cognitive_annotation"},
    "mateo": {
        "read_brief", "read_cognitive_annotation",
        "write_prototype_file", "write_task_artifact", "web_search",
    },
    "ingrid": {"read_prototype_file", "read_task_artifact", "write_review"},
}


def require_tool(agent_name: str, tool: str) -> None:
    """Raise PermissionError if `agent_name` is not permitted to use `tool`."""
    allowed = PERMITTED_TOOLS.get(agent_name)
    if allowed is None:
        raise PermissionError(f"Unknown agent '{agent_name}' has no permitted_tools entry")
    if tool not in allowed:
        raise PermissionError(
            f"Agent '{agent_name}' is not permitted to use tool '{tool}' "
            f"(permitted: {sorted(allowed)})"
        )
