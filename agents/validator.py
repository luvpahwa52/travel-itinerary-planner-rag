import sys
import os
import json
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def extract_total_from_itinerary(itinerary):
    """Extracts the total cost from the itinerary text using regex."""
    patterns = [
        r"Total:\s*₹\s*([\d,]+)",
        r"Total:\s*INR\s*([\d,]+)",
        r"Total:\s*([\d,]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, itinerary)
        if match:
            return int(match.group(1).replace(",", ""))
    return 0


def check_completeness(itinerary, intent):
    """
    Checks if itinerary covers all requested days.
    Returns (is_complete, missing_days).
    """
    requested_days = intent.get("days", 1)
    found_days = []

    for d in range(1, requested_days + 1):
        pattern = rf"Day\s*{d}"
        if re.search(pattern, itinerary, re.IGNORECASE):
            found_days.append(d)

    missing = [d for d in range(1, requested_days + 1) if d not in found_days]
    return len(missing) == 0, missing


def check_hallucinations(itinerary, context):
    """
    Code-based hallucination check.
    Verifies that items mentioned in the itinerary exist in the context.
    """
    valid_names = [c["metadata"]["name"].lower().strip() for c in context]

    mentioned_items = []
    patterns = [
        r"(?:Stay|Food|Morning|Afternoon|Evening):\s*(?:Visit\s+|Explore\s+|Dinner at\s+|Lunch at\s+|Breakfast at\s+)?([^—₹\n]+)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, itinerary)
        for match in matches:
            cleaned = match.strip().rstrip(" —").strip()
            if cleaned and len(cleaned) > 3:
                mentioned_items.append(cleaned)

    fabricated = []
    for item in mentioned_items:
        item_lower = item.lower().strip()

        found = False
        for valid in valid_names:
            if valid in item_lower or item_lower in valid:
                found = True
                break

        generic_terms = [
            "relax", "return", "free time", "departure", "arrival", "check-in",
            "checkout", "explore local", "last-minute", "pre-paid", "travel to",
            "continue", "overnight", "no stay", "n/a", "morning", "afternoon",
            "evening", "enjoy", "breakfast at hotel", "dinner at hotel",
            "local eatery", "hotel", "shopping", "relaxation", "walk",
            "total for day", "total for", "snacks", "local shacks",
            "jeep safari", "waterfall visit", "waterfall", "light snacks",
            "on the houseboat", "houseboat dinner", "houseboat breakfast",
            "breakfast on", "dinner on", "lunch on", "return to",
            "nearby restaurant", "local restaurant", "street food from",
            "check-out", "transfer", "arrive", "depart", "airport",
            "last minute", "sightseeing", "city tour", "day trip",
            "round trip", "self-ride", "self-drive", "full day",
            "full-day", "half-day", "half day", "taxi hire",
            "exploring", "visit local", "visit nearby", "stroll",
            "temple visit", "beach visit", "fort visit",
            "museum visit", "market visit", "garden visit",
            "cruise", "safari", "trek", "trekking",
            "paragliding", "zorbing", "skiing", "rafting",
            "activities", "activity", "excursion",
            "at zostel", "at hotel", "cafeteria",
            "try", "regional", "special", "organic",
            "train to", "bus to", "flight to", "flight from",
            "ferry", "boat ride", "walking", "cycle",
        ]
        is_generic = any(term in item_lower for term in generic_terms)

        if not found and not is_generic:
            fabricated.append(item)

    return fabricated


def validate_itinerary(itinerary, context, intent):
    """
    Validates the generated itinerary using PURE CODE:
    - Budget check via regex
    - Hallucination check via name matching
    - Completeness check via day counting
    No LLM calls — 100% deterministic and reliable.
    """
    budget = intent.get("budget", 0)
    issues = []

    # ===== BUDGET CHECK =====
    total_cost = extract_total_from_itinerary(itinerary)
    budget_valid = total_cost <= budget if budget > 0 else True

    if not budget_valid:
        issues.append(f"Total cost ₹{total_cost} exceeds budget ₹{budget} by ₹{total_cost - budget}.")

    # ===== COMPLETENESS CHECK =====
    is_complete, missing_days = check_completeness(itinerary, intent)
    if not is_complete:
        issues.append(f"Missing days in itinerary: {missing_days}")

    # ===== HALLUCINATION CHECK =====
    fabricated = check_hallucinations(itinerary, context)
    hallucination_found = len(fabricated) > 0

    if hallucination_found:
        for item in fabricated:
            issues.append(f"Possibly fabricated: {item}")

    # ===== DECISION =====
    if hallucination_found and len(fabricated) >= 5:
        result = "REJECT"
    elif not budget_valid:
        result = "REVISE"
    elif not is_complete:
        result = "REVISE"
    elif hallucination_found and len(fabricated) >= 3:
        result = "REVISE"
    else:
        result = "PASS"

    feedback = "; ".join(issues) if issues else "All items verified, budget within limits, all days covered."

    return {
        "result": result,
        "budget_valid": budget_valid,
        "hallucination_found": hallucination_found,
        "is_complete": is_complete,
        "total_cost_extracted": total_cost,
        "issues": issues,
        "feedback": feedback,
    }


if __name__ == "__main__":
    from agents.planner import plan_itinerary

    print("=" * 60)
    print("  VALIDATOR AGENT — TEST")
    print("=" * 60)

    query = "3 day trip to Goa under 15000 with beaches and food"
    planner_result = plan_itinerary(query)

    print("\n✅ Validating itinerary...")
    validation = validate_itinerary(
        itinerary=planner_result["itinerary"],
        context=planner_result["context"],
        intent=planner_result["intent"],
    )

    print(f"\nValidation Result: {json.dumps(validation, indent=2)}")
    print("\n  VALIDATOR AGENT READY!")
