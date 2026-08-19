"""Image generation helper (OpenAI Images API), used by the Developer agent
for visuals the Claude API can't produce directly (e.g. team avatars)."""
import base64
import os

from openai import OpenAI


def generate_image(prompt: str, output_path: str, size: str = "1024x1024") -> None:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size=size,
        n=1,
    )
    image_bytes = base64.b64decode(response.data[0].b64_json)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(image_bytes)


def edit_image(
    source_path: str, prompt: str, output_path: str, size: str = "1024x1024"
) -> None:
    """Edit an existing image instead of generating a fresh one.

    Use this for *adjustments* to an image that already exists -- a different
    expression on an approved portrait, a tweak to an approved layout. A fresh
    generate_image() call with an adjusted prompt produces a different person
    or composition, because nothing carries over between generations; an edit
    keeps the source and changes what the prompt asks for.

    Added 2026-08-19 when the founder asked for an approved headshot candidate
    to look "a little friendlier" -- regenerating would have changed the face.
    """
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    with open(source_path, "rb") as source:
        response = client.images.edit(
            model="gpt-image-1",
            image=source,
            prompt=prompt,
            size=size,
            n=1,
        )
    image_bytes = base64.b64decode(response.data[0].b64_json)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(image_bytes)
