import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import pandas as pd
from pathlib import Path
from embeddings.embedder import build_movie_text

# Path where ChromaDB saves data on disk
CHROMA_PATH = Path("../../data/embeddings/chroma_db")
COLLECTION_NAME = "movies"


def get_chroma_client():
    """
    Return a persistent ChromaDB client.
    Data is stored in data/embeddings/chroma_db/ and survives notebook restarts.
    """
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_PATH))


def get_collection(client=None, reset=False):
    """
    Get or create the movies collection.

    Args:
        client: a ChromaDB client (creates one if not provided)
        reset: if True, deletes the existing collection and starts fresh

    Returns:
        ChromaDB collection object
    """
    if client is None:
        client = get_chroma_client()

    # Use the same model as embedder.py so vectors are compatible
    ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"Deleted existing collection '{COLLECTION_NAME}'")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}  # use cosine similarity
    )
    return collection


def add_movies_to_collection(df, collection, batch_size=100):
    """
    Add movies from a pandas DataFrame to the ChromaDB collection.

    Each movie becomes one document. The text is the combination of
    title + overview + genres. The metadata stores structured fields
    so we can filter later (e.g., only action movies from the 2000s).

    Args:
        df: cleaned movies DataFrame
        collection: ChromaDB collection
        batch_size: how many movies to add in one API call
    """
    existing_ids = set(collection.get()["ids"])
    print(f"Collection already has {len(existing_ids)} movies")

    documents, metadatas, ids = [], [], []

    for _, row in df.iterrows():
        movie_id = f"tmdb_{int(row['tmdb_id'])}" if 'tmdb_id' in row else f"row_{row.name}"

        if movie_id in existing_ids:
            continue  # skip movies already in the collection

        text = build_movie_text(row)
        if not text or text == 'Unknown movie':
            continue

        meta = {
            "title":    str(row.get("title", "Unknown"))[:500],
            "year":     int(row["release_year"]) if pd.notna(row.get("release_year")) else 0,
            "genre":    str(row.get("primary_genre", "Unknown"))[:100],
            "language": str(row.get("original_language", "en"))[:10],
            "rating":   float(row["vote_average"]) if pd.notna(row.get("vote_average")) else 0.0,
            "revenue":  float(row["revenue_usd"]) if pd.notna(row.get("revenue_usd")) else 0.0,
        }

        documents.append(text)
        metadatas.append(meta)
        ids.append(movie_id)

        # Add in batches to avoid memory issues with large datasets
        if len(documents) >= batch_size:
            collection.add(documents=documents, metadatas=metadatas, ids=ids)
            documents, metadatas, ids = [], [], []

    # Add any remaining movies
    if documents:
        collection.add(documents=documents, metadatas=metadatas, ids=ids)

    total = collection.count()
    print(f"Collection now contains {total} movies")
    return total
