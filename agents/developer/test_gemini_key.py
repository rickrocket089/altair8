"""One-off smoke test for the newly added GEMINI_API_KEY -- confirms the key
works before it gets wired into any real behavioral-test script (Sprint 6
follow-up / Sprint 7 planning).
"""
import os

from dotenv import load_dotenv
from google import genai

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))


def run() -> None:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents="Reply with exactly one short sentence confirming you received this test message.",
    )
    print(f"[Gemini test] {response.text}")


if __name__ == "__main__":
    run()
