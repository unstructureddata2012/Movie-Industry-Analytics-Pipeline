from sentence_transformers import SentenceTransformer
import numpy as np

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None  # lazy loading - only download when first needed


def get_model():
    """Return the sentence-transformer model, loading it on first call."""
    global _model
    if _model is None:
        print(f"Loading model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        print("Model loaded successfully")
    return _model


def build_movie_text(row):
    """
    Create a single text string from a movie row.
    We combine title, overview, and genres so the embedding captures
    all useful information about the movie.
    """
    parts = []
    if 'title' in row and str(row['title']) != 'nan':
        parts.append(str(row['title']))
    if 'overview' in row and str(row['overview']) != 'nan':
        parts.append(str(row['overview']))
    if 'genres' in row and str(row['genres']) != 'nan':
        parts.append(f"Genres: {row['genres']}")
    return ' | '.join(parts) if parts else 'Unknown movie'


def embed_texts(texts, batch_size=64, normalize=True):
    """
    Generate embeddings for a list of text strings.

    Args:
        texts: list of strings to embed
        batch_size: how many texts to process at once (64 is a good default)
        normalize: if True, embeddings are scaled to unit length,
                   which makes cosine similarity equal to dot product

    Returns:
        numpy array of shape (len(texts), 384)
    """
    model = get_model()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=normalize,
        show_progress_bar=len(texts) > 100
    )
    return embeddings


def embed_single(text, normalize=True):
    """
    Generate an embedding for a single text string.
    Useful for embedding a search query.
    """
    model = get_model()
    return model.encode(text, normalize_embeddings=normalize)
