import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.bedrock_client import call_llm


SUPERVISOR_SYSTEM_PROMPT = """You are a Travel Supervisor Agent. Your job is to extract structured travel intent from the user's query.

Extract the following fields:
- city: The destination city (e.g., Goa, Delhi, Jaipur, Kerala, Manali, Varanasi)
- days: Number of days for the trip (integer)
- budget: Total budget in INR (integer). If not mentioned, set to 0.
- interests: List of interests like ["beach", "food", "heritage", "adventure", "shopping", "nature", "religious"]

IMPORTANT:
- If the user doesn't mention a field, make a reasonable guess based on context.
- If the user mentions a specific budget number (e.g., "under 15000", "within 20000"), ALWAYS use that exact number.
- Only if NO number is mentioned, then guess: "budget trip" = 10000, "mid-range" = 25000, "luxury" = 50000.
- Always respond with ONLY valid JSON, no extra text.

Example:
User: "3 day budget trip to Goa with beaches and nightlife"
Response: {"city": "Goa", "days": 3, "budget": 10000, "interests": ["beach", "nightlife"]}
"""


def extract_intent(user_query):
    """
    Extracts structured travel intent from user query using LLM.

    Args:
        user_query: Raw user input (e.g., "3 day Goa trip under 15000")

    Returns:
        dict with keys: city, days, budget, interests
    """
    response = call_llm(user_query, system_prompt=SUPERVISOR_SYSTEM_PROMPT)

    # Clean response — remove markdown code blocks if any
    response = response.strip()
    if response.startswith("```"):
        response = response.split("\n", 1)[1]
        response = response.rsplit("```", 1)[0]
    response = response.strip()

    try:
        intent = json.loads(response)
    except json.JSONDecodeError:
        # Fallback if LLM doesn't return clean JSON
        intent = {
            "city": "Goa",
            "days": 3,
            "budget": 15000,
            "interests": ["sightseeing"],
        }
        print(f"Warning: Could not parse LLM response, using defaults. Raw: {response}")

    return intent


if __name__ == "__main__":
    print("=" * 60)
    print("  SUPERVISOR AGENT — INTENT EXTRACTION TEST")
    print("=" * 60)

    test_queries = [
        "3 day budget trip to Goa with beaches and food",
        "Plan a 5 day luxury Jaipur trip focused on heritage and shopping",
        "Weekend trip to Manali under 8000 for adventure activities",
        "I want to visit Varanasi for 2 days, interested in temples and street food",
    ]

    for query in test_queries:
        print(f"\nQuery: \"{query}\"")
        intent = extract_intent(query)
        print(f"Intent: {json.dumps(intent, indent=2)}")
        print("-" * 60)

    print("\n  SUPERVISOR AGENT READY!")
