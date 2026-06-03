import sys
import os
import json
import sqlite3
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.bedrock_client import call_llm


SCORER_SYSTEM_PROMPT = """You are a Travel Itinerary Scorer Agent. Score the faithfulness and quality of a generated itinerary against its source context.

SCORING CRITERIA:
1. FACTUAL ACCURACY (30%): Are all places, costs, and descriptions matching the context?
2. RELEVANCE (25%): How relevant is the itinerary to the user's original question and interests?
3. SOURCE COVERAGE (25%): Does the itinerary use diverse sources (attractions, hotels, food, transport)?
4. BUDGET ADHERENCE (10%): Is the total cost within the user's budget?
5. COMPLETENESS (10%): Does the itinerary cover all requested days with morning/afternoon/evening activities?

Respond with ONLY valid JSON:
{
    "faithfulness_score": 0.0 to 1.0,
    "relevance_score": 0.0 to 1.0,
    "factual_accuracy": 0.0 to 1.0,
    "source_coverage": 0.0 to 1.0,
    "budget_adherence": 0.0 to 1.0,
    "completeness": 0.0 to 1.0,
    "reasoning": "Brief explanation of scores"
}
"""

DB_PATH = "db/feedback.db"


def init_feedback_db():
    os.makedirs("db", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itinerary_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_query TEXT,
            city TEXT,
            days INTEGER,
            budget INTEGER,
            itinerary TEXT,
            faithfulness_score REAL,
            relevance_score REAL,
            source_coverage REAL,
            overall_accuracy REAL,
            confidence_level TEXT,
            validation_result TEXT,
            sources_used TEXT,
            use_case TEXT DEFAULT 'Travel Itinerary Planner',
            user_rating INTEGER DEFAULT 0,
            user_feedback TEXT DEFAULT '',
            disclaimer TEXT DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()


def calculate_source_coverage(context):
    """Calculates what % of source types (attractions, hotels, food, transport) are covered."""
    all_sources = {"attractions", "hotels", "food", "transport"}
    used_sources = set([c["metadata"]["source"] for c in context])
    coverage = len(used_sources.intersection(all_sources)) / len(all_sources)
    return round(coverage, 2)


def score_itinerary(itinerary, context, intent):
    """
    Scores the faithfulness and quality of the generated itinerary.
    Returns faithfulness_score, relevance_score, source_coverage, overall_accuracy, confidence_level, disclaimer.
    """
    context_text = "\n\n".join(
        [f"[Source: {c['metadata']['source']}] [Name: {c['metadata']['name']}] {c['document'][:200]}" for c in context]
    )

    prompt = f"""
Score the following itinerary:

USER INTENT:
- City: {intent.get('city', 'Unknown')}
- Days: {intent.get('days', 'Unknown')}
- Budget: INR {intent.get('budget', 0)}
- Interests: {intent.get('interests', [])}

GENERATED ITINERARY:
{itinerary}

SOURCE CONTEXT DATA:
{context_text}

Score and respond with JSON only.
"""

    response = call_llm(prompt, system_prompt=SCORER_SYSTEM_PROMPT)

    response = response.strip()
    if response.startswith("```"):
        response = response.split("\n", 1)[1]
        response = response.rsplit("```", 1)[0]
    response = response.strip()

    try:
        scores = json.loads(response)
    except json.JSONDecodeError:
        scores = {
            "faithfulness_score": 0.75,
            "relevance_score": 0.75,
            "factual_accuracy": 0.75,
            "source_coverage": 0.75,
            "budget_adherence": 0.75,
            "completeness": 0.75,
            "reasoning": "Score parse error — defaulting to 0.75",
        }

    # Calculate source coverage from actual context
    actual_coverage = calculate_source_coverage(context)
    scores["source_coverage"] = actual_coverage

    # Calculate overall accuracy (weighted average)
    fa = scores.get("factual_accuracy", 0.75)
    rel = scores.get("relevance_score", 0.75)
    sc = actual_coverage
    ba = scores.get("budget_adherence", 0.75)
    comp = scores.get("completeness", 0.75)

    overall = round((fa * 0.30) + (rel * 0.25) + (sc * 0.25) + (ba * 0.10) + (comp * 0.10), 2)
    scores["overall_accuracy"] = overall

    # Confidence level
    if overall >= 0.85:
        scores["confidence_level"] = "HIGH"
    elif overall >= 0.70:
        scores["confidence_level"] = "MEDIUM"
    else:
        scores["confidence_level"] = "LOW"

    # Low confidence disclaimer
    if scores["confidence_level"] == "LOW":
        scores["disclaimer"] = "⚠️ Lower confidence score. Some recommendations may need verification. Please cross-check before booking."
    else:
        scores["disclaimer"] = ""

    return scores


def log_to_db(user_query, intent, itinerary, scores, validation_result, sources_used):
    """Logs the itinerary and scores to SQLite."""
    init_feedback_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO itinerary_logs (
            timestamp, user_query, city, days, budget, itinerary,
            faithfulness_score, relevance_score, source_coverage, overall_accuracy,
            confidence_level, validation_result, sources_used, use_case, disclaimer
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        user_query,
        intent.get("city", "Unknown"),
        intent.get("days", 0),
        intent.get("budget", 0),
        itinerary,
        scores.get("faithfulness_score", 0),
        scores.get("relevance_score", 0),
        scores.get("source_coverage", 0),
        scores.get("overall_accuracy", 0),
        scores.get("confidence_level", "UNKNOWN"),
        validation_result,
        json.dumps(sources_used),
        "Travel Itinerary Planner",
        scores.get("disclaimer", ""),
    ))
    conn.commit()
    log_id = cursor.lastrowid
    conn.close()
    return log_id


def save_user_feedback(log_id, rating, feedback=""):
    """Saves user feedback (1-5 stars) for a generated itinerary."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE itinerary_logs SET user_rating = ?, user_feedback = ? WHERE id = ?
    """, (rating, feedback, log_id))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    from agents.planner import plan_itinerary

    print("=" * 60)
    print("  SCORER AGENT — TEST")
    print("=" * 60)

    query = "3 day trip to Goa under 15000 with beaches and food"
    planner_result = plan_itinerary(query)

    print("\n📊 Scoring itinerary...")
    scores = score_itinerary(
        itinerary=planner_result["itinerary"],
        context=planner_result["context"],
        intent=planner_result["intent"],
    )

    print(f"\nScores: {json.dumps(scores, indent=2)}")

    sources_used = list(set([c["metadata"]["name"] for c in planner_result["context"]]))
    log_id = log_to_db(
        user_query=query,
        intent=planner_result["intent"],
        itinerary=planner_result["itinerary"],
        scores=scores,
        validation_result="PASS",
        sources_used=sources_used,
    )
    print(f"\nLogged to SQLite — ID: {log_id}")
    print("  SCORER AGENT READY!")
