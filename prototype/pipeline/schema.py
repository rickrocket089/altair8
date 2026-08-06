"""The intermediate representation Sprint 8's pipeline stages produce and
consume. Stage 4 (the renderer) materializes a PipelineDocument -- it does
not generate new content, only renders what's already here. This is the
schema Ingrid required before any code was written (Sprint 8 prototype
proposal review, review_id 12/13): without it, the renderer would inevitably
be written as a direct HTML generator, coupling the pipeline to one output
medium.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class VisualSlot:
    slot_id: str
    spec_type: str  # "vega-lite" | "svg-placeholder"
    spec: dict
    caption: str
    audience_note: str
    illustrative: bool = True  # v1 is Path A only (LLM-synthesized data) -- always True for now
    generator_model: str = ""  # which LLM produced this spec, for the Stage 2 reliability log
    validation_passed: bool | None = None  # structural validity (Question 1 -- see reliability_log.py)
    content_grounded: bool | None = None  # topic coherence (a different question -- see content_grounding.py)
    grounding_issues: list[str] = field(default_factory=list)


@dataclass
class SectionNode:
    id: str
    title: str
    prose_blocks: list[str] = field(default_factory=list)
    visual_slots: list[VisualSlot] = field(default_factory=list)
    navigation_anchors: list[str] = field(default_factory=list)


@dataclass
class PipelineDocument:
    title: str
    audience: str
    goal: str
    sections: list[SectionNode] = field(default_factory=list)
    global_notes: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def all_visual_slots(self) -> dict[str, VisualSlot]:
        return {vs.slot_id: vs for s in self.sections for vs in s.visual_slots}
