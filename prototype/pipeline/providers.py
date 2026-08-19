"""Thin per-stage LLM provider abstraction (design principle #2: the
solution must not be bound to any single foundation model). Each pipeline
stage is configured with a provider name; swapping a stage's model means
changing its config, not its code.

The Stage 2 (Visual Asset Generator) default model is an explicitly
UNTESTED assumption per Ingrid's review -- see visual_asset_generator.py's
reliability log, which is meant to validate or overturn this default during
real v1 runs, not just assert it.
"""
import base64
import os

from anthropic import Anthropic
from openai import OpenAI

_anthropic_client = None
_openai_client = None


def _anthropic() -> Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _anthropic_client


def _openai() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _openai_client


def complete(provider: str, model: str, system: str, prompt: str, max_tokens: int = 2000) -> str:
    """Single-turn completion, provider-agnostic. `provider` is 'anthropic' or 'openai'."""
    if provider == "anthropic":
        response = _anthropic().messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "\n".join(b.text for b in response.content if b.type == "text")
    elif provider == "openai":
        response = _openai().chat.completions.create(
            model=model,
            max_completion_tokens=max_tokens,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    else:
        raise ValueError(f"Unknown provider '{provider}' -- expected 'anthropic' or 'openai'")


def complete_with_image(
    provider: str, model: str, system: str, prompt: str, image_path: str, max_tokens: int = 2000
) -> str:
    """Single-turn completion with one image attached (vision input).

    Anthropic only for now -- this is a new capability added for the
    template-reproduction test, not a general pipeline stage yet. Extending
    to GPT-5.2/Gemini vision is a natural follow-up, not done here (same
    kind of explicit scope-narrowing Ingrid has required elsewhere, applied
    up front instead of after the fact).
    """
    if provider != "anthropic":
        raise ValueError("complete_with_image currently only supports provider='anthropic'")
    ext = os.path.splitext(image_path)[1].lower()
    media_type = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(
        ext, "image/png"
    )
    with open(image_path, "rb") as f:
        image_b64 = base64.standard_b64encode(f.read()).decode("utf-8")
    response = _anthropic().messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return "\n".join(b.text for b in response.content if b.type == "text")


# Per-stage default config. Change a stage's model here, not in the stage's
# own code -- that's the whole point of the abstraction.
STAGE_CONFIG = {
    "planner": {"provider": "anthropic", "model": "claude-sonnet-4-6"},
    "writer": {"provider": "anthropic", "model": "claude-sonnet-4-6"},
    # UNTESTED DEFAULT (Ingrid's review, review_id 12): justified only by
    # prior experience, not evidence. v1 logs validation failure rate per
    # model so this can be revised based on real data, not asserted.
    "visual_asset_generator": {"provider": "openai", "model": "gpt-5.2"},
}
