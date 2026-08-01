"""Shared scope-completeness checklist for "full market/landscape analysis"
research briefs.

Context: Sprint 2's landscape scan and Sprint 3's Genially deep-dive were
both scoped to third-party consumer tools (Gamma, Tome, Genially, ...) and
silently never covered the foundation-model providers' own first-party
capabilities -- a real category, not a detail, missing from what was
presented as a broad market scan. Nobody caught it: Sophie scoped the
sprint question narrowly without noticing, and Ingrid's review checks
evidentiary rigor of what was submitted, not whether an entire category was
silently out of scope. The founder caught it, not the team (2026-07-23).

This module is the fix: a required-category checklist any "full market
analysis" sprint question must be checked against, plus a cheap automatic
keyword-coverage pre-check that catches an obvious miss before Ingrid's
qualitative review even runs. It does not replace Ingrid's judgment -- a
keyword match can be superficial (mentioning "Anthropic" once is not the
same as actually assessing Anthropic's capabilities) -- it's a fast,
deterministic first pass that flags likely gaps for her to look at
specifically, the same "deterministic vs. judgment call" split Mateo's
Sprint 4 review argued for regarding executable validators generally.
"""
import re

MARKET_ANALYSIS_CATEGORIES = {
    "third_party_tools": {
        "label": "Third-party tools/products",
        "description": "Commercial or consumer products built on top of foundation models (e.g. Genially, Gamma, Tome, Beautiful.ai, Flourish, Prezi).",
        "keywords": ["genially", "gamma", "tome", "beautiful.ai", "flourish", "prezi", "canva"],
    },
    "foundation_model_native": {
        "label": "Foundation-model providers' own first-party capabilities",
        "description": "Native capabilities shipped by the model providers themselves, not third-party products built on top of them (e.g. Anthropic's Claude skills, OpenAI's ChatGPT Canvas, Google's Gemini Canvas, Microsoft Copilot).",
        "keywords": ["anthropic", "claude", "openai", "chatgpt", "gpt-", "google", "gemini", "microsoft", "copilot"],
    },
    "open_source_frameworks": {
        "label": "Open-source / research frameworks",
        "description": "Non-commercial frameworks or research codebases relevant to the problem (e.g. AI-Scientist-v2, RISE).",
        "keywords": ["github", "open-source", "open source", "framework", "repository", "repo"],
    },
    "academic_research": {
        "label": "Academic / independent research",
        "description": "Published literature on the underlying problem, independent of any specific product or vendor.",
        "keywords": ["arxiv", "paper", "study", "research literature", "published", "academic"],
    },
}


def check_category_coverage(text: str) -> dict:
    """Cheap keyword-based pre-check. Returns {category_key: bool} -- True
    means at least one keyword was found, NOT that the category was
    actually assessed with rigor. A False strongly suggests a real gap; a
    True still needs Ingrid's qualitative judgment on whether the mention
    was substantive or incidental.
    """
    lowered = text.lower()
    return {
        key: any(re.search(re.escape(kw), lowered) for kw in cat["keywords"])
        for key, cat in MARKET_ANALYSIS_CATEGORIES.items()
    }


def format_coverage_report(text: str) -> str:
    coverage = check_category_coverage(text)
    lines = ["Scope-completeness pre-check (keyword-based, not a substitute for judgment):"]
    for key, cat in MARKET_ANALYSIS_CATEGORIES.items():
        status = "mentioned" if coverage[key] else "NO MENTION FOUND -- likely gap"
        lines.append(f"- {cat['label']}: {status}")
    return "\n".join(lines)
