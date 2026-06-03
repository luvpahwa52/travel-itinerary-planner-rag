import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.bedrock_client import call_llm
from agents.retriever import retrieve
from agents.supervisor import extract_intent


PLANNER_SYSTEM_PROMPT = """You are a Travel Planner Agent. You create detailed day-wise travel itineraries based ONLY on the provided context data.

STRICT RULES:
1. Use ONLY the information from the provided context. Do NOT make up places, hotels, restaurants, or prices.
2. Every place, hotel, restaurant, and cost you mention MUST come from the context.
3. Create a day-wise itinerary with morning, afternoon, and evening activities.
4. Include a budget breakdown at the end showing: attractions, food, hotel, transport costs.
5. Total cost MUST stay within the user's budget.
6. Cite the source for each recommendation (e.g., [Source: attractions] or [Source: food]).

CRITICAL BUDGET RULES:
7. BEFORE choosing a hotel, calculate: hotel_cost × number_of_nights. If this ALONE exceeds 40% of the total budget, pick a CHEAPER hotel from the context.
8. NEVER assign a hotel/restaurant to a city or location that doesn't match the context data. If a hotel is listed for "Alleppey", do NOT use it for "Munnar".
9. ONLY use hotels that exist in the context for the EXACT city mentioned. Do NOT fabricate hotel locations.

OUTPUT FORMAT:
---
📍 Trip: {city} | {days} Days | Budget: ₹{budget}

🗓️ Day 1: {title}
  🌅 Morning: {activity} — ₹{cost} [Source: {source}]
  🌞 Afternoon: {activity} — ₹{cost} [Source: {source}]
  🌆 Evening: {activity} — ₹{cost} [Source: {source}]
  🍽️ Food: {restaurant} — ₹{cost} [Source: {source}]
  🏨 Stay: {hotel} — ₹{cost}/night [Source: {source}]

... (repeat for each day)

💰 Budget Breakdown:
  Attractions: ₹{total}
  Food: ₹{total}
  Hotels: ₹{total}
  Transport: ₹{total}
  ─────────────────
  Total: ₹{grand_total}
  Remaining: ₹{budget - grand_total}

📋 Sources Used: {list all source names}
---

If the budget is too low for the requested days, suggest a realistic adjustment.
"""


def plan_itinerary(user_query):
    """
    Full pipeline: Query → Supervisor → Retriever → Planner → Itinerary

    Args:
        user_query: Raw user input (e.g., "3 day Goa trip under 15000")

    Returns:
        dict with keys: intent, context, itinerary
    """
    # Step 1: Extract intent via Supervisor
    print("\n🧠 Supervisor extracting intent...")
    intent = extract_intent(user_query)
    print(f"   City: {intent['city']} | Days: {intent['days']} | Budget: ₹{intent['budget']}")
    print(f"   Interests: {intent['interests']}")

    # Step 2: Retrieve relevant context from ChromaDB
    print("\n🔍 Retriever fetching context...")

    # Fetch from all sources for comprehensive itinerary
    all_context = []

    # Get attractions
    attractions = retrieve(user_query, city=intent["city"], source="attractions", top_k=5)
    all_context.extend(attractions)

    # Get hotels
    hotels = retrieve(user_query, city=intent["city"], source="hotels", top_k=3)
    all_context.extend(hotels)

    # Get food
    food = retrieve(user_query, city=intent["city"], source="food", top_k=3)
    all_context.extend(food)

    # Get transport
    transport = retrieve(user_query, city=intent["city"], source="transport", top_k=3)
    all_context.extend(transport)

    print(f"   Retrieved {len(all_context)} chunks (attractions: {len(attractions)}, hotels: {len(hotels)}, food: {len(food)}, transport: {len(transport)})")

    # Step 3: Build context string for the Planner LLM
    context_text = "\n\n".join(
        [f"[Source: {c['metadata']['source']}] {c['document']}" for c in all_context]
    )

    # Step 4: Generate itinerary via Planner LLM
    print("\n✍️  Planner generating itinerary...")
    planner_prompt = f"""
User Request: {user_query}

Extracted Intent:
- City: {intent['city']}
- Days: {intent['days']}
- Budget: ₹{intent['budget']}
- Interests: {', '.join(intent['interests'])}

Available Context Data:
{context_text}

Generate a detailed day-wise travel itinerary following your output format. Use ONLY the data provided above.
"""

    itinerary = call_llm(planner_prompt, system_prompt=PLANNER_SYSTEM_PROMPT)

    return {
        "intent": intent,
        "context": all_context,
        "itinerary": itinerary,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("  PLANNER AGENT — FULL PIPELINE TEST")
    print("=" * 60)

    query = "3 day budget trip to Goa under 15000 with beaches and food"
    result = plan_itinerary(query)

    print("\n" + "=" * 60)
    print("  GENERATED ITINERARY")
    print("=" * 60)
    print(result["itinerary"])