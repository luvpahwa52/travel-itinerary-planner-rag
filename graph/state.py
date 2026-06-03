from typing import TypedDict, List, Dict, Any


class TravelState(TypedDict):
    """Shared state passed between all agents in the LangGraph workflow."""

    # Input
    user_query: str

    # Supervisor output
    intent: Dict[str, Any]

    # Retriever output
    context: List[Dict[str, Any]]

    # Planner output
    itinerary: str

    # Validator output
    validation_result: str
    validation_feedback: str
    is_complete: bool

    # Scorer output
    faithfulness_score: float
    relevance_score: float
    source_coverage: float
    overall_accuracy: float
    confidence_level: str
    disclaimer: str

    # Tracking
    revision_count: int
    sources_used: List[str]
    log_id: int
