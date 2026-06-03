import pandas as pd
import chromadb
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.embeddings import get_embedding_function


def load_data():
    attractions = pd.read_csv("data/attractions.csv")
    hotels = pd.read_csv("data/hotels.csv")
    food = pd.read_csv("data/food.csv")
    transport = pd.read_csv("data/transport.csv")
    return attractions, hotels, food, transport


def create_chunks(attractions, hotels, food, transport):
    documents = []
    metadatas = []
    ids = []

    for i, row in attractions.iterrows():
        doc = (
            f"{row['name']} is a {row['category']} attraction in {row['city']}. "
            f"{row['description']} "
            f"Entry cost is INR {row['entry_cost_inr']}. "
            f"Time needed: {row['time_needed_hrs']} hours. "
            f"Best time to visit: {row['best_time']}. "
            f"Rating: {row['rating']}/5."
        )
        documents.append(doc)
        metadatas.append({
            "source": "attractions",
            "city": row["city"],
            "category": row["category"],
            "name": row["name"],
            "cost": float(row["entry_cost_inr"]),
            "rating": float(row["rating"]),
        })
        ids.append(f"attraction_{i}")

    for i, row in hotels.iterrows():
        doc = (
            f"{row['name']} is a {row['type']} hotel in {row['city']} ({row['area']} area). "
            f"{row['description']} "
            f"Price: INR {row['price_per_night_inr']} per night. "
            f"Rating: {row['rating']}/5."
        )
        documents.append(doc)
        metadatas.append({
            "source": "hotels",
            "city": row["city"],
            "category": row["type"],
            "name": row["name"],
            "cost": float(row["price_per_night_inr"]),
            "rating": float(row["rating"]),
        })
        ids.append(f"hotel_{i}")

    for i, row in food.iterrows():
        doc = (
            f"{row['name']} is a {row['type']} in {row['city']} serving {row['cuisine']} cuisine. "
            f"{row['description']} "
            f"Must try: {row['must_try']}. "
            f"Average cost for two: INR {row['avg_cost_for_two_inr']}. "
            f"Rating: {row['rating']}/5."
        )
        documents.append(doc)
        metadatas.append({
            "source": "food",
            "city": row["city"],
            "category": row["cuisine"],
            "name": row["name"],
            "cost": float(row["avg_cost_for_two_inr"]),
            "rating": float(row["rating"]),
        })
        ids.append(f"food_{i}")

    for i, row in transport.iterrows():
        doc = (
            f"{row['mode']} in {row['city']}: {row['description']} "
            f"Route: {row['route']}. "
            f"Average cost: INR {row['avg_cost_inr']} {row['cost_unit']}."
        )
        documents.append(doc)
        metadatas.append({
            "source": "transport",
            "city": row["city"],
            "category": row["mode"],
            "name": row["mode"],
            "cost": float(row["avg_cost_inr"]),
            "rating": 0.0,
        })
        ids.append(f"transport_{i}")

    return documents, metadatas, ids


def build_chroma_db(documents, metadatas, ids):
    embed_fn = get_embedding_function()

    client = chromadb.PersistentClient(path="db/chroma_store")

    try:
        client.delete_collection("travel_knowledge")
        print("Deleted existing collection.")
    except Exception:
        pass

    collection = client.create_collection(
        name="travel_knowledge",
        metadata={"description": "Travel data for Indian cities"},
    )

    batch_size = 50
    for start in range(0, len(documents), batch_size):
        end = min(start + batch_size, len(documents))
        batch_docs = documents[start:end]
        batch_meta = metadatas[start:end]
        batch_ids = ids[start:end]

        embeddings = embed_fn(batch_docs)

        collection.add(
            documents=batch_docs,
            embeddings=embeddings,
            metadatas=batch_meta,
            ids=batch_ids,
        )
        print(f"  Added batch {start}-{end} ({end - start} docs)")

    return collection


def test_query(collection):
    embed_fn = get_embedding_function()

    print("\n" + "=" * 50)
    print("TEST QUERY: \"Budget beach trip in Goa\"")
    print("=" * 50)

    query_embedding = embed_fn(["Budget beach trip in Goa"])
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=5,
        include=["documents", "metadatas", "distances"],
    )

    for i, (doc, meta, dist) in enumerate(
        zip(results["documents"][0], results["metadatas"][0], results["distances"][0])
    ):
        print(f"\n--- Result {i+1} (distance: {dist:.4f}) ---")
        print(f"Source: {meta['source']} | City: {meta['city']} | Name: {meta['name']}")
        print(f"Text: {doc[:150]}...")


if __name__ == "__main__":
    print("=" * 50)
    print("  BUILDING TRAVEL KNOWLEDGE VECTOR DATABASE")
    print("=" * 50)

    print("\nLoading CSVs...")
    attractions, hotels, food, transport = load_data()
    print(f"  Attractions: {len(attractions)} | Hotels: {len(hotels)} | Food: {len(food)} | Transport: {len(transport)}")

    print("\nCreating text chunks...")
    documents, metadatas, ids = create_chunks(attractions, hotels, food, transport)
    print(f"  Total chunks: {len(documents)}")

    print("\nEmbedding & storing in ChromaDB...")
    collection = build_chroma_db(documents, metadatas, ids)
    print(f"\nChromaDB built! Total documents: {collection.count()}")

    test_query(collection)
