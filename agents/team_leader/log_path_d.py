"""Record Path D and the founder's working assumption of 2026-09-15."""
import io

from tools import db

doc = io.open(
    "/app/workspace/outputs/paths/path-d-interrogable-narrative.md", encoding="utf-8"
).read()
db.set_memory("team_leader", "path_d_interrogable_narrative", doc)
print("path D stored:", len(doc), "chars")

aid = db.create_candidate_approach(
    title="Path D -- the interrogable narrative (agent stays resident in the communication)",
    description=(
        "Founder, 2026-09-15. Business communication has a sender and a receiver, and "
        "that asymmetry is why we present at all. Because the artifact can answer "
        "nothing at the moment a question is asked, the sender builds an appendix -- "
        "backup slides are materialised anticipation of questions. This path keeps an "
        "agent resident in the artifact so the reader can change resolution at will: "
        "zoom into a claim to reach its evidence, zoom out to see where it sits, ask "
        "why something is asserted, in real time.\n\n"
        "Supported in our own record by Genially's documented ceiling (Sprint 3: "
        "navigation topology 100% author-scripted at creation time, no runtime "
        "conditional logic -- the closest analogue fails on exactly this axis), by "
        "Naledi's Sprint 9 meta-finding that the real innovations across five fields "
        "are new reader-artifact relationships rather than new chart shapes, and by "
        "hypothesis 3 having sat in the record since August with no evidence for or "
        "against it at all.\n\n"
        "Resolves unstated bet A (is the single artifact the right unit?) in the "
        "negative, deliberately rather than by drift -- the first of the three bets to "
        "be decided in the open.\n\n"
        "FOUR KILL CRITERIA: liability (the agent answers in the sender's name to "
        "things the sender never saw, and backup slides are not only anticipated but "
        "vetted); grounding (Sprint 8 showed the pipeline inventing content that was "
        "structurally perfect -- live answering means live invention in front of a "
        "client); asymmetry is sometimes the point (unstated bet B: a sender may not "
        "want the receiver zooming into the assumptions, which may make the path right "
        "and unsellable in the segments that pay); latency.\n\n"
        "SMALLEST TESTABLE VERSION: take one real document, let the reader open any "
        "claim to the layer beneath it, and PRECOMPUTE AND VET every answer -- nothing "
        "generated at read time. That separates 'is interrogable depth valuable' "
        "(testable with five people in two to three weeks) from 'can an agent be "
        "trusted to answer live' (the hard question, not required for the first). It "
        "also removes the liability criterion entirely, and it is reachable from the "
        "direction the founder actually chose: if the sender builds the backup "
        "material in advance anyway, making it navigable in place rather than appended "
        "behind is this path's precomputed form.\n\n"
        "Reframes backlog #23: the question becomes not only whether the model picks "
        "the right FORM but whether it picks the right DEPTH on demand. Recasts C1 "
        "from an artifact format into the governance layer of a live medium.\n\n"
        "STATUS: parked by founder decision on the day it was raised, not rejected. "
        "Full write-up at workspace/outputs/paths/path-d-interrogable-narrative.md and "
        "in agent memory team_leader/path_d_interrogable_narrative, including the "
        "conditions under which it returns."
    ),
    category="product-path",
    source_reference="workspace/outputs/paths/path-d-interrogable-narrative.md",
    flagged_by="founder",
    sprint_id=db.get_sprint_id(11),
    priority="high",
)
print("candidate approach #%d logged" % aid)

db.set_memory(
    "team_leader",
    "working_assumptions",
    "WORKING ASSUMPTION, set by the founder 2026-09-15:\n\n"
    "The sender builds in advance what they want to communicate. Authoring "
    "happens before the communication, not during it.\n\n"
    "This is a deliberate, provisional choice made on the same day the founder "
    "raised the alternative himself (an agent that stays resident in the "
    "communication and answers at read time -- Path D, candidate approach "
    "logged, parked not rejected). His words: set my ideas aside for now, go "
    "with the sender-builds-in-advance concept, then we will see.\n\n"
    "IT IS RECORDED HERE BECAUSE IT DECIDES SOMETHING THE PROGRAMME HAD NEVER "
    "SAID OUT LOUD. Ingrid's audit of the same day named three bets the "
    "programme was making silently, the first being that the single artifact "
    "is the right unit of business communication. This assumption resolves "
    "that bet in the affirmative, for now, knowingly. Her instruction was that "
    "these be recorded so a path which quietly resolves one of them can be "
    "caught doing it. This is that record.\n\n"
    "What it does NOT decide: whether the artifact, once built in advance, has "
    "to be read linearly. Path D's precomputed variant -- pre-built, vetted "
    "depth that the reader navigates in place instead of an appendix appended "
    "behind -- sits inside this assumption rather than outside it.\n\n"
    "To be revisited when the conditions in "
    "workspace/outputs/paths/path-d-interrogable-narrative.md section 9 are met.",
)
print("working assumption recorded")

db.set_memory(
    "team_leader",
    "current_focus",
    "2026-09-15. Sprint 11 closed (C1 built, browser-verified, three blocks "
    "fixed under Ingrid's gate). No sprint is open, and none is to be opened "
    "until the founder decides -- his explicit instruction.\n\n"
    "The programme is mid-turn: from a research cadence toward analysing "
    "concrete paths to a product. Anchors were fixed first so criteria cannot "
    "later be retrofitted to a favourite -- hypotheses 5-8 written with "
    "evidence status attached, hypothesis 1 rewritten to something that can "
    "fail, and the three previously unstated bets recorded. All of it audited "
    "by Ingrid the same day; her corrections were applied rather than argued "
    "with.\n\n"
    "Open in front of the founder: design criteria to be worked out before the "
    "paths are described (K1a expressive ceiling vs K1b the agent's reliable "
    "generation ceiling, audience/goal dependence, reader-side control, "
    "content truthfulness -- each needing a test and a known failing example, "
    "and gates to be kept separate from weights).\n\n"
    "Blocking, per Ingrid, before any path commitment: backlog #15. Diagnosed "
    "2026-09-15 as mostly an infrastructure defect rather than a procurement "
    "problem -- the IEEE connector has been returning 403 since it was written "
    "(zero IEEE papers of 1017 retrieved), and the OpenAlex connector was "
    "discarding venue, year and open-access full-text links, so retrieved ACM "
    "and IEEE work was indistinguishable from noise. Connector fixed and "
    "verified; ACM DL full texts remain the genuine procurement question. The "
    "first filtered query immediately surfaced uncertainty-visualization work "
    "in IEEE TVCG that bears directly on C1's novelty claim and that this team "
    "had never seen.",
)
print("current focus updated")
