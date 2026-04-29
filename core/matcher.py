import numpy as np

def cosine(a, b):
    """Calculate cosine similarity between two embeddings."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def find_match(query, db, k=3):
    """Find top K matches in the database for a query embedding."""
    scores = []
    for name, emb in db:
        score = cosine(query, emb)
        scores.append((name, score))
    
    # Sort by similarity score descending (highest similarity first)
    return sorted(scores, key=lambda x: x[1], reverse=True)[:k]
