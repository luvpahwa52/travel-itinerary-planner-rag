import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, END
from graph.state import TravelState
from agents.supervisor import extract_intent
from agents.retriever import retrieve
from agents.validator import validate_itinerary
from agents.scorer import score_itinerary, log_to_db
from utils.bedrock_client import call_llm
from agents.planner import PLANNER_SYSTEM_PROMPT


MAX_REVISIONS = 2


def supervisor_node(state: TravelState) -> dict:
    print("\n🧠 [SUPERVISOR] Extracting intent...")
    intent = extract_intent(state["user_query"])
    print(f"   City: {intent['city']} | Days: {intent['days']} | Budget: ₹{intent['budget']}")
    print(f"   Interests: {intent['interests']}")
    return {"intent": intent}


def retriever_node(state: TravelState) -> dict:
    print("\n🔍 [RETRIEVER] Fetching context from ChromaDB...")
    intent = state["intent"]
    query = state["user_query"]

    all_context = []
    all_context.extend(retrieve(query, city=intent["city"], source="attractions", top_k=5))
    all_context.extend(retrieve(query, city=intent["city"], source="hotels", top_k=3))
    all_context.extend(retrieve(query, city=intent["city"], source="food", top_k=3))
    all_context.extend(retrieve(query, city=intent["city"], source="transport", top_k=3))

    sources = list(set([c["metadata"]["name"] for c in all_context]))
    print(f"   Retrieved {len(all_context)} chunks | Sources: {len(sources)}")
    return {"context": all_context, "sources_used": sources}


def planner_node(state: TravelState) -> dict:
    revision = state.get("revision_count", 0)

    if revision == 0:
        print("\n✍️  [PLANNER] Generating itinerary...")
    else:
        print(f"\n✍️  [PLANNER] Revising itinerary (attempt {revision + 1})...")

    intent = state["intent"]
    context = state["context"]

    context_text = "\n\n".join(
        [f"[Source: {c['metadata']['source']}] {c['document']}" for c in context]
    )

    revision_note = ""
    if revision > 0 and state.get("validation_feedback"):
        revision_note = f"""

REVISION REQUIRED — Fix these issues from the validator:
{state['validation_feedback']}

Make corrections and regenerate the itinerary.
"""

    prompt = f"""
User Request: {state['user_query']}

Extracted Intent:
- City: {intent['city']}
- Days: {intent['days']}
- Budget: ₹{intent['budget']}
- Interests: {', '.join(intent['interests'])}

Available Context Data:
{context_text}
{revision_note}
Generate a detailed day-wise travel itinerary following your output format. Use ONLY the data provided above.
"""

    itinerary = call_llm(prompt, system_prompt=PLANNER_SYSTEM_PROMPT)
    print("   Itinerary generated!")
    return {"itinerary": itinerary, "revision_count": revision + 1}


def validator_node(state: TravelState) -> dict:
    print("\n✅ [VALIDATOR] Checking itinerary...")
    validation = validate_itinerary(
        itinerary=state["itinerary"],
        context=state["context"],
        intent=state["intent"],
    )

    result = validation.get("result", "PASS")
    feedback = validation.get("feedback", "")
    issues = validation.get("issues", [])
    is_complete = validation.get("is_complete", True)

    print(f"   Result: {result}")
    if issues:
        for issue in issues:
            print(f"   ⚠️  {issue}")

    return {
        "validation_result": result,
        "validation_feedback": feedback,
        "is_complete": is_complete,
    }


def scorer_node(state: TravelState) -> dict:
    print("\n📊 [SCORER] Scoring itinerary...")
    scores = score_itinerary(
        itinerary=state["itinerary"],
        context=state["context"],
        intent=state["intent"],
    )

    overall = scores.get("overall_accuracy", 0)
    confidence = scores.get("confidence_level", "UNKNOWN")
    disclaimer = scores.get("disclaimer", "")

    print(f"   Faithfulness:    {scores.get('faithfulness_score', 0):.0%}")
    print(f"   Relevance:       {scores.get('relevance_score', 0):.0%}")
    print(f"   Source Coverage:  {scores.get('source_coverage', 0):.0%}")
    print(f"   Overall Accuracy: {overall:.0%} ({confidence})")
    if disclaimer:
        print(f"   {disclaimer}")

    log_id = log_to_db(
        user_query=state["user_query"],
        intent=state["intent"],
        itinerary=state["itinerary"],
        scores=scores,
        validation_result=state["validation_result"],
        sources_used=state.get("sources_used", []),
    )
    print(f"   Logged to SQLite — ID: {log_id}")

    return {
        "faithfulness_score": scores.get("faithfulness_score", 0),
        "relevance_score": scores.get("relevance_score", 0),
        "source_coverage": scores.get("source_coverage", 0),
        "overall_accuracy": overall,
        "confidence_level": confidence,
        "disclaimer": disclaimer,
        "log_id": log_id,
    }


def should_continue(state: TravelState) -> str:
    result = state.get("validation_result", "PASS")
    revision = state.get("revision_count", 0)

    if result == "PASS":
        return "scorer"
    elif result == "REVISE" and revision < MAX_REVISIONS:
        print(f"   🔄 Sending back to Planner for revision (attempt {revision + 1}/{MAX_REVISIONS})")
        return "planner"
    else:
        if revision >= MAX_REVISIONS:
            print(f"   ⚠️  Max revisions ({MAX_REVISIONS}) reached — proceeding to scorer")
        else:
            print(f"   ❌ REJECTED — proceeding to scorer with current output")
        return "scorer"


def build_workflow():
    workflow = StateGraph(TravelState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("scorer", scorer_node)

    workflow.set_entry_point("supervisor")
    workflow.add_edge("supervisor", "retriever")
    workflow.add_edge("retriever", "planner")
    workflow.add_edge("planner", "validator")

    workflow.add_conditional_edges(
        "validator",
        should_continue,
        {
            "planner": "planner",
            "scorer": "scorer",
        },
    )

    workflow.add_edge("scorer", END)

    return workflow.compile()


def run_travel_planner(user_query):
    app = build_workflow()

    initial_state = {
        "user_query": user_query,
        "intent": {},
        "context": [],
        "itinerary": "",
        "validation_result": "",
        "validation_feedback": "",
        "is_complete": True,
        "faithfulness_score": 0.0,
        "relevance_score": 0.0,
        "source_coverage": 0.0,
        "overall_accuracy": 0.0,
        "confidence_level": "",
        "disclaimer": "",
        "revision_count": 0,
        "sources_used": [],
        "log_id": 0,
    }

    final_state = app.invoke(initial_state)
    return final_state


if __name__ == "__main__":
    print("=" * 60)
    print("  🚀 MULTI-AGENT TRAVEL PLANNER — FULL WORKFLOW")
    print("=" * 60)

    query = "3 day trip to Goa under 15000 with beaches and food"
    print(f"\n📝 User Query: \"{query}\"")

    result = run_travel_planner(query)

    print("\n" + "=" * 60)
    print("  📋 FINAL OUTPUT")
    print("=" * 60)
    print(result["itinerary"])

    print("\n" + "-" * 60)
    print(f"  Validation:       {result['validation_result']}")
    print(f"  Faithfulness:     {result['faithfulness_score']:.0%}")
    print(f"  Relevance:        {result['relevance_score']:.0%}")
    print(f"  Source Coverage:   {result['source_coverage']:.0%}")
    print(f"  Overall Accuracy:  {result['overall_accuracy']:.0%} ({result['confidence_level']})")
    print(f"  Sources Used:     {len(result['sources_used'])}")
    print(f"  Revisions:        {result['revision_count']}")
    if result.get("disclaimer"):
        print(f"  ⚠️  {result['disclaimer']}")
    print("-" * 60)
