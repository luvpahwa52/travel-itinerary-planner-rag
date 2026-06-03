import chromadb
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.embeddings import get_embedding_function
from utils.config import CHROMA_DB_PATH, COLLECTION_NAME, TOP_K_RESULTS

RELEVANCE_THRESHOLD = 1.3


def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)
    return collection


def retrieve(query, city=None, source=None, top_k=TOP_K_RESULTS):
    collection = get_collection()
    embed_fn = get_embedding_function()
    query_embedding = embed_fn([query])

    where_filter = None
    if city and source:
        where_filter = {"$and": [{"city": city}, {"source": source}]}
    elif city:
        where_filter = {"city": city}
    elif source:
        where_filter = {"source": source}

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    formatted = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        if dist <= RELEVANCE_THRESHOLD:
            formatted.append({
                "document": doc,
                "metadata": meta,
                "distance": round(dist, 4),
            })

    if not formatted:
        for doc, meta, dist in zip(
            results["documents"][0][:3],
            results["metadatas"][0][:3],
            results["distances"][0][:3],
        ):
            formatted.append({
                "document": doc,
                "metadata": meta,
                "distance": round(dist, 4),
            })

    return formatted


def print_results(results, query):
    print(f"\nQuery: \"{query}\"")
    print(f"Results: {len(results)} (after relevance filtering)")
    print("=" * 60)
    for i, r in enumerate(results):
        print(f"\n--- Result {i+1} (distance: {r['distance']}) ---")
        print(f"Source: {r['metadata']['source']} | City: {r['metadata']['city']} | Name: {r['metadata']['name']}")
        print(f"Cost: INR {r['metadata']['cost']} | Rating: {r['metadata']['rating']}")
        print(f"Text: {r['document'][:200]}...")


if __name__ == "__main__":
    print("=" * 60)
    print("  RETRIEVER AGENT — TEST QUERIES")
    print("=" * 60)

    r1 = retrieve("Budget beach trip in Goa")
    print_results(r1, "Budget beach trip in Goa")

    r2 = retrieve("Best places to visit", city="Jaipur")
    print_results(r2, "Best places to visit [city=Jaipur]")

    r3 = retrieve("Cheap food in Delhi", source="food")
    print_results(r3, "Cheap food in Delhi [source=food]")

    r4 = retrieve("Luxury stay", city="Mumbai", source="hotels")
    print_results(r4, "Luxury stay [city=Mumbai, source=hotels]")

    print("\n" + "=" * 60)
    print("  RETRIEVER AGENT READY!")
    print("=" * 60)
