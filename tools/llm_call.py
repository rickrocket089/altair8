"""One call site for "stream a message and get the complete text back,"
so truncation handling exists once instead of being reinvented (or
forgotten) per script.

Built 2026-09-16 after the truncation trap hit four different scripts in
one sprint -- two caught by a manual `stop_reason` check that had to be
copy-pasted into each script, one caught only by eye (missing sections),
and one continuation that got all the way to fabricating a sample size and
design structure that didn't exist, because it was grounded in a ~1200-char
tail excerpt instead of the real source material. This is the "rules
without enforcement recur" pattern from Process Review #3, applied to
Claude API calls specifically: `if resp.stop_reason == "max_tokens":` was
being re-added by hand to every new script, which means every new script
could just as easily forget it again.

The fix that actually closes the gap: don't hand-extract a tail excerpt
and re-explain context to a continuation call. Instead, replay the FULL
original conversation (system prompt + all messages, unchanged) with the
partial reply appended as an assistant turn and a plain "continue exactly
where you left off" user turn appended after it. The original messages
already contain whatever source material grounded the first attempt, so
grounding is automatic rather than something each call site has to
remember to reconstruct. This is the practical form of the "Continuation
Grounding" principle in tools/principles.md.
"""
from dataclasses import dataclass, field


@dataclass
class CompletionResult:
    text: str
    input_tokens: int
    output_tokens: int
    stop_reason: str
    continuations: int = 0
    # Per-call token counts, for scripts that want the detail rather than
    # just the totals (e.g. to sanity-check how much a continuation cost).
    calls: list = field(default_factory=list)


def stream_complete(
    client,
    *,
    model: str,
    max_tokens: int,
    system: str,
    messages: list[dict],
    max_continuations: int = 4,
) -> CompletionResult:
    """Drop-in replacement for the

        with client.messages.stream(model=..., max_tokens=..., system=..., messages=...) as stream:
            resp = stream.get_final_message()
        text = resp.content[0].text

    pattern used throughout agents/. If the response is truncated
    (stop_reason == "max_tokens"), automatically continues -- replaying the
    full conversation plus the partial reply -- up to `max_continuations`
    times, concatenating the text. Raises RuntimeError if still truncated
    after the continuation budget is exhausted, rather than silently
    returning an incomplete document (the whole point of this function is
    that a caller never has to remember to check for that itself).
    """
    working_messages = list(messages)
    full_text = ""
    total_input = 0
    total_output = 0
    calls = []
    stop_reason = "max_tokens"

    for attempt in range(max_continuations + 1):
        with client.messages.stream(
            model=model, max_tokens=max_tokens, system=system, messages=working_messages,
        ) as stream:
            resp = stream.get_final_message()

        chunk = resp.content[0].text
        full_text += chunk
        total_input += resp.usage.input_tokens
        total_output += resp.usage.output_tokens
        calls.append({"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens})
        stop_reason = resp.stop_reason

        if stop_reason != "max_tokens":
            break

        # Continuation Grounding: replay the *original* messages (which
        # still carry whatever source document grounded this call) plus
        # what's been generated so far, rather than summarizing or
        # excerpting. This is the fix -- a continuation with the full
        # source in context has something to check new claims against; one
        # given only a tail excerpt does not.
        working_messages = list(messages) + [
            {"role": "assistant", "content": full_text},
            {"role": "user", "content": (
                "Continue exactly where you left off -- your previous reply "
                "was cut off at a token limit mid-thought. Do not repeat, "
                "summarize, or restate anything you already wrote. Do not "
                "introduce new facts, numbers, or claims that aren't "
                "already grounded in the material you were given above."
            )},
        ]

    if stop_reason == "max_tokens":
        raise RuntimeError(
            f"Still truncated after {max_continuations} continuations "
            f"({len(full_text)} chars so far). Raise max_tokens, raise "
            f"max_continuations, or split the task -- do not silently "
            f"return a partial document."
        )

    return CompletionResult(
        text=full_text,
        input_tokens=total_input,
        output_tokens=total_output,
        stop_reason=stop_reason,
        continuations=len(calls) - 1,
        calls=calls,
    )
