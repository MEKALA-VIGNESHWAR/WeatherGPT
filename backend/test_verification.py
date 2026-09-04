import asyncio
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from app.schemas.chat import ChatRequest
from app.ai.orchestrator import orchestrator

async def run_tests():
    tests = [
        "1. Will it rain today?",
        "2. Will it rain tomorrow?",
        "3. Is there any chance of rain in the next 4 days?",
        "4. Which day has the highest chance of rain?",
        "5. When is rain most likely?",
        "6. Will it rain tomorrow evening?",
        "7. Should I carry an umbrella tomorrow?",
        "8. Which day is best for an outdoor activity?",
        "9. Compare rain chances for the next 4 days.",
        "10. What's the weather tomorrow?"
    ]

    for t in tests:
        num, q = t.split(". ", 1)
        print(f"\n==========================================", flush=True)
        print(f"TEST {num}: {q}", flush=True)
        req = ChatRequest(message=q, location_name="Hyderabad", latitude=17.385, longitude=78.4867)
        resp = await orchestrator.process_query(req)
        print(f"Location: {resp.location}", flush=True)
        print(f"Sources: {resp.sources}", flush=True)
        print(f"Confidence: {resp.confidence}", flush=True)
        print(f"Answer:\n{resp.answer}", flush=True)

if __name__ == "__main__":
    asyncio.run(run_tests())
