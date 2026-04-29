import numpy as np

def cosine(a, b):
    """Calculate cosine similarity between two embeddings."""
    # Ensure they are normalized for simple dot product
    # But np.linalg.norm is safer if they aren't
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0
    return np.dot(a, b) / (norm_a * norm_b)

def find_match(face_query, clip_query, db, k=3):
    """
    Find top K matches in the database using combined Face and CLIP scores.
    db entry: (name, face_emb, clip_emb)
    """
    scores = []
    for entry in db:
        # Support both old format (name, emb) and new format (name, face_emb, clip_emb)
        if len(entry) == 3:
            name, face_emb, clip_emb = entry
            
            # Phase 2: Combined Scoring
            face_score = cosine(face_query, face_emb)
            clip_score = cosine(clip_query, clip_emb)
            
            # 50% Face + 50% CLIP
            final_score = (0.5 * face_score) + (0.5 * clip_score)
        else:
            # Fallback for old database format
            name, face_emb = entry
            final_score = cosine(face_query, face_emb)
            
        scores.append((name, final_score))
    
    # Sort by similarity score descending
    return sorted(scores, key=lambda x: x[1], reverse=True)[:k]
