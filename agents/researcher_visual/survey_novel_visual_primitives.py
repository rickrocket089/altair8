"""Sprint 9, Phase A: Naledi surveys adjacent fields for visual-communication
patterns that exploit zoom, motion, true multi-dimensionality, or
interactivity (design principle #4) but were never applied to business
communication.

SCOPE DECLARATION: covered = data journalism, motion graphics/explainer
design, spatial/AR interfaces, game UI/HUD design, scientific visualization
beyond standard charts. Excluded = classic infovis research literature
(Sprint 5's domain) and graphic-design theory without a communication angle.

METHOD NOTE: Naledi does not have web_search permission (agents/permissions.py)
-- this survey draws on the model's own trained knowledge of these fields,
not live-verified sources. That's appropriate for Phase A's divergent/
synthesis nature, but any candidate promoted into Phase B (Mateo's actual
build) should have Kenji verify it against real, named, current examples
first -- this script says so explicitly rather than presenting the catalog
as independently verified.
"""
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from agents.permissions import require_tool
from agents.researcher_visual.persona import NAME, SYSTEM_PROMPT
from tools import db, vectorstore

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))

FIELDS = [
    "Data journalism (e.g. NYT Interactive, FT Visual & Data Journalism, The Pudding, Bloomberg Graphics)",
    "Motion graphics / explainer video design",
    "Spatial / AR interfaces (data rooms, spatial dashboards, exhibition wayfinding)",
    "Game UI / HUD design (progressive disclosure, diegetic information)",
    "Scientific visualization beyond standard charts (network/graph visualization, simulation rendering, molecular visualization)",
]


def run() -> None:
    require_tool("naledi", "write_cognitive_annotation")
    db.set_memory("naledi", "status", "online")
    sprint_id = db.get_sprint_id(9)
    task_id = db.create_task(
        created_by="team_leader",
        assigned_to="naledi",
        title="Sprint 9 Phase A: survey adjacent fields for novel visual-communication patterns",
        description="Catalog 8-12 concrete patterns from 5 named fields, per design principle #4.",
    )

    hypotheses = db.get_memory("team_leader", "hypotheses") or ""
    design_principles = db.get_memory("team_leader", "design_principles") or ""

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Sprint 9 Phase A. The founder's own framing: we keep "
                    "finding the same business-chart taxonomy (bar/line/pie/"
                    "map/flowchart) even when testing whether models reason "
                    "well about form -- Sprint 6/7/8 all operated within it. "
                    "Design principle #4 commits us to something bigger: "
                    "the full range of what's possible, not just better "
                    "selection within existing formats. This sprint looks "
                    "OUTSIDE business communication for patterns that "
                    "already demonstrate that range.\n\n"
                    f"THE TEAM'S HYPOTHESES:\n{hypotheses}\n\n"
                    f"THE TEAM'S DESIGN PRINCIPLES:\n{design_principles}\n\n"
                    "SCOPE -- survey exactly these 5 fields, nothing else:\n"
                    + "\n".join(f"- {f}" for f in FIELDS) + "\n\n"
                    "For EACH field, name 1-3 concrete, specific patterns "
                    "(not vague categories -- name the actual technique, "
                    "e.g. 'scrollytelling with pinned/sticky visual state "
                    "while text scrolls past' is a pattern; 'good "
                    "storytelling' is not). For each pattern:\n\n"
                    "1. NAME the specific technique.\n"
                    "2. WHAT AUDIENCE/GOAL NEED it serves -- be concrete "
                    "about why this technique exists in its original field "
                    "(what problem was it solving there).\n"
                    "3. DOES BUSINESS COMMUNICATION LACK AN EQUIVALENT -- be "
                    "honest here. Some patterns from these fields (e.g. "
                    "basic hover tooltips) already exist in business "
                    "dashboards. Only flag genuine gaps.\n"
                    "4. PORTABILITY -- your honest first estimate of "
                    "whether this could be adapted to a real business "
                    "content scenario without requiring infrastructure "
                    "business tools don't have (e.g. a technique requiring "
                    "a VR headset is a real pattern but low-portability for "
                    "v1; a technique requiring only a browser and a JS "
                    "charting library is high-portability).\n\n"
                    "Target: 8-12 patterns total across the 5 fields (not "
                    "necessarily evenly distributed -- some fields may "
                    "yield more than others, say so if one field comes up "
                    "thin).\n\n"
                    "IMPORTANT METHODOLOGICAL CAVEAT to include explicitly "
                    "in your own output: you do not have live web search "
                    "access for this task. Everything here is drawn from "
                    "your own trained knowledge of these fields, not "
                    "verified against current, named, real examples. Say "
                    "this plainly, and flag which 2-3 patterns you're most "
                    "confident actually exist versus which are more "
                    "speculative-but-plausible extrapolations -- so Kenji "
                    "knows what most needs verification before Phase B "
                    "commits real build effort to anything.\n\n"
                    "End with your own recommendation: which patterns look "
                    "most promising for Phase B (Mateo's prototype "
                    "selection), against the criteria already set (solves a "
                    "real audience/goal gap; technically buildable without "
                    "special infrastructure; categorically different from "
                    "existing chart types, not just styling) -- and be "
                    "honest if you think the yield this round is thin "
                    "against those criteria, since that's itself a "
                    "legitimate finding, not a failure to hide."
                ),
            }
        ],
    ) as stream:
        response = stream.get_final_message()
    catalog = response.content[0].text
    db.log_usage("naledi", response.usage.input_tokens, response.usage.output_tokens)

    vectorstore.remember(
        collection_name="researcher_memory",
        doc_id=f"novel-visual-primitives-survey-task-{task_id}",
        text=catalog,
        metadata={"agent": "naledi", "type": "novel_visual_primitives_survey"},
    )
    db.set_memory("naledi", "novel_visual_primitives_survey", catalog)
    db.update_task(
        task_id, status="completed", result=catalog,
        artifact_type="research_brief",
        artifact_payload={"memory_key": "naledi/novel_visual_primitives_survey"},
    )

    print(f"[{NAME}] Sprint 9 Phase A survey complete.\n\n{catalog}")


if __name__ == "__main__":
    run()
