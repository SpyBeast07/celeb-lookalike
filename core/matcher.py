import numpy as np

def cosine(a, b):
    """Calculate cosine similarity between two embeddings."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def find_top_k(query, db, k=3):
    """Find top K matches in the database for a query embedding."""
    scores = []
    for name, emb in db:
        score = cosine(query, emb)
        scores.append((name, score))
    
    # Sort by similarity score descending
    return sorted(scores, key=lambda x: x[1], reverse=True)[:k]
