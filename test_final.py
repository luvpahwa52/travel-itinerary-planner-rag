import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from graph.workflow import run_travel_planner


def run_test(query, test_num):
    print("\n" + "=" * 70)
    print(f"  TEST {test_num}: \"{query}\"")
    print("=" * 70)

    result = run_travel_planner(query)

    print("\n" + "-" * 70)
    print("  📋 GENERATED ITINERARY")
    print("-" * 70)
    print(result["itinerary"])

    print("\n" + "-" * 70)
    print("  📊 RESULTS SUMMARY")
    print("-" * 70)
    print(f"  City:             {result['intent'].get('city', 'N/A')}")
    print(f"  Days:             {result['intent'].get('days', 'N/A')}")
    print(f"  Budget:           ₹{result['intent'].get('budget', 'N/A')}")
    print(f"  Interests:        {result['intent'].get('interests', [])}")
    print(f"  Validation:       {result['validation_result']}")
    print(f"  Faithfulness:     {result['faithfulness_score']:.0%}")
    print(f"  Relevance:        {result['relevance_score']:.0%}")
    print(f"  Source Coverage:   {result['source_coverage']:.0%}")
    print(f"  Overall Accuracy:  {result['overall_accuracy']:.0%} ({result['confidence_level']})")
    print(f"  Sources Used:     {len(result['sources_used'])}")
    print(f"  Revisions:        {result['revision_count']}")
    if result.get("disclaimer"):
        print(f"  ⚠️  {result['disclaimer']}")
    print("-" * 70)

    return result


if __name__ == "__main__":
    print("=" * 70)
    print("  🧪 FINAL COMPREHENSIVE TEST — ALL 10 CITIES")
    print("=" * 70)

    test_queries = [
        # Original 6 cities
        "3 day trip to Goa under 15000 with beaches and seafood",
        "2 day trip to Delhi under 5000 for heritage and street food",
        "2 day trip to Jaipur under 10000 for forts and shopping",
        "3 day trip to Kerala under 18000 with backwaters and nature",
        "2 day trip to Manali under 8000 for adventure and cafes",
        "2 day trip to Varanasi under 6000 for temples and boat ride",

        "2 day trip to Mumbai under 8000 for landmarks and street food",
        "3 day trip to Udaipur under 12000 for lakes and heritage",
        "2 day trip to Rishikesh under 6000 for rafting and yoga",
        "1 day trip to Agra under 5000 for Taj Mahal and Mughlai food",
    ]

    results_summary = []

    for i, query in enumerate(test_queries, 1):
        result = run_test(query, i)
        results_summary.append({
            "test": i,
            "city": result["intent"].get("city", "N/A"),
            "budget": result["intent"].get("budget", 0),
            "validation": result["validation_result"],
            "faith": f"{result['faithfulness_score']:.0%}",
            "relev": f"{result['relevance_score']:.0%}",
            "cover": f"{result['source_coverage']:.0%}",
            "overall": f"{result['overall_accuracy']:.0%}",
            "conf": result["confidence_level"],
            "rev": result["revision_count"],
        })

    print("\n\n" + "=" * 90)
    print("  📊 FINAL COMPREHENSIVE TEST — ALL 10 CITIES SUMMARY")
    print("=" * 90)
    print(f"  {'#':<4} {'City':<12} {'Budget':<10} {'Valid':<8} {'Faith':<8} {'Relev':<8} {'Cover':<8} {'Overall':<10} {'Conf':<8} {'Rev':<4}")
    print("  " + "-" * 80)
    for r in results_summary:
        print(f"  {r['test']:<4} {r['city']:<12} ₹{r['budget']:<9} {r['validation']:<8} {r['faith']:<8} {r['relev']:<8} {r['cover']:<8} {r['overall']:<10} {r['conf']:<8} {r['rev']:<4}")

    passed = sum(1 for r in results_summary if r["validation"] == "PASS")
    print("\n" + "=" * 90)
    print(f"  PASSED: {passed}/{len(results_summary)} | TOTAL TESTS: {len(results_summary)}")
    print("=" * 90)
