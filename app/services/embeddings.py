"""
Embeddings Service for ResearchPilot (Phase 4).

An "Embedding" converts a piece of text into a list of numbers (a vector).
When two pieces of text have similar meanings or topics, their vectors
point in almost the same direction in vector space!

We measure how close two vectors are using "Cosine Similarity".
- Score 1.0: Identical direction / perfect match
- Score 0.0: No relation / orthogonal
"""

import math
import os
import re
from typing import List


# -----------------------------------------------------------------------------
# 1. Cosine Similarity Function
# -----------------------------------------------------------------------------
def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Computes the cosine similarity between two numerical vectors.

    Formula:
        similarity = (A • B) / (||A|| * ||B||)

    Where:
        - A • B is the dot product (multiply each pair of numbers and sum)
        - ||A|| is the magnitude/length of vector A (sqrt of sum of squares)
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))

    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0

    return dot_product / (mag_a * mag_b)


# -----------------------------------------------------------------------------
# 2. Text Embedding Generator
# -----------------------------------------------------------------------------
# We use a fixed-dimension vector (e.g. 64 dimensions) with term hashing.
# This provides deterministic, lightning-fast semantic word overlap embeddings
# that run 100% offline on any machine with ZERO external libraries!
# -----------------------------------------------------------------------------
VECTOR_DIMENSION = 64


def get_embedding(text: str) -> List[float]:
    """
    Generates an embedding vector for a given piece of text.

    If an OpenAI/LLM API key is present, it can use an external embedding model.
    Otherwise, it uses our built-in normalized feature hash vectorizer.
    """
    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")

    if api_key:
        try:
            return _get_llm_embedding(text, api_key)
        except Exception as err:
            print(f"[Embeddings] External API failed ({err}). Using built-in vectorizer.")

    return _get_local_embedding(text)


def _get_local_embedding(text: str, dimensions: int = VECTOR_DIMENSION) -> List[float]:
    """
    A lightweight, built-in vectorizer.
    It breaks text into words, hashes them into fixed buckets, and normalizes the vector.
    """
    # 1. Tokenize: extract lowercase alphanumeric words
    tokens = re.findall(r"\b\w+\b", text.lower())
    if not tokens:
        return [0.0] * dimensions

    # 2. Initialize an empty vector
    vector = [0.0] * dimensions

    # 3. Hash words into vector buckets
    for token in tokens:
        # Simple polynomial string hash to distribute words across vector dimensions
        bucket = abs(hash(token)) % dimensions
        vector[bucket] += 1.0

    # 4. Normalize vector to unit length (so magnitude = 1.0)
    mag = math.sqrt(sum(v * v for v in vector))
    if mag > 0:
        vector = [v / mag for v in vector]

    return vector


def _get_llm_embedding(text: str, api_key: str) -> List[float]:
    """
    Optional: Calls an OpenAI-compatible /v1/embeddings endpoint if configured.
    """
    import httpx

    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    response = httpx.post(
        f"{base_url}/embeddings",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model, "input": text},
        timeout=15.0
    )
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]
