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
