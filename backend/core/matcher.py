import numpy as np

def cosine(a, b):
    """Calculate cosine similarity between two embeddings."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0
    return np.dot(a, b) / (norm_a * norm_b)

def find_match(face_query, user_gender, user_age, landmark_query, db, category_filter=None, k=5):
    """
    Phase 9: Separate Pipelines
    Supports filtering by category (actors vs cartoons).
    """
    scores = []
    for entry in db:
        # entry: (name, face_emb, landmark_vec, gender, age, category)
        if len(entry) == 6:
            name, face_emb, celeb_landmark, celeb_gender, celeb_age, category = entry
        elif len(entry) == 5:
            name, face_emb, celeb_landmark, celeb_gender, celeb_age = entry
            category = 'actors' # Default fallback
        else:
            name, face_emb = entry[:2]
            celeb_landmark = None
            celeb_gender, celeb_age = 0, 0
            category = 'actors'
            
        # 1. Filter by category if requested
        if category_filter and category != category_filter:
            continue
            
        # 2. Embedding Similarity (60%)
        emb_sim = cosine(face_query, face_emb)
        
        # 3. Landmark Similarity (40%)
        landmark_sim = 0.0
        if landmark_query is not None and celeb_landmark is not None:
            q_vec = np.array(landmark_query)
            c_vec = np.array(celeb_landmark)
            dist = np.linalg.norm(q_vec - c_vec)
            landmark_sim = max(0.0, 1.0 - dist)
        else:
            landmark_sim = emb_sim

        # 4. Phase 8: Attribute Matching (Penalties)
        penalty = 0.0
        
        # Gender Penalty (-0.3) - Only apply for 'actors' category
        if category == 'actors' and user_gender != celeb_gender:
            penalty += 0.3
            
        # Age Group Penalty (-0.1) - Only apply for 'actors'
        if category == 'actors':
            age_diff = abs(user_age - celeb_age)
            if age_diff > 15:
                penalty += 0.1
        
        # Base hybrid score
        base_score = (0.6 * emb_sim) + (0.4 * landmark_sim)
        
        # Final Score with Penalty
        final_score = max(0.0, base_score - penalty)
            
        scores.append((name, final_score))
    
    return sorted(scores, key=lambda x: x[1], reverse=True)[:k]
