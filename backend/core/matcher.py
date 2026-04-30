import numpy as np

def cosine(a, b):
    """Calculate cosine similarity between two embeddings."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0
    return np.dot(a, b) / (norm_a * norm_b)

def find_match(face_query, user_gender, user_age, landmark_query, db, k=5):
    """
    Phase 5: Hybrid Similarity Engine
    Score = 0.6 * Embedding Similarity + 0.4 * Landmark Similarity
    """
    scores = []
    for entry in db:
        # entry: (name, face_emb, landmark_vec, gender, age)
        if len(entry) == 5:
            name, face_emb, celeb_landmark, celeb_gender, celeb_age = entry
        elif len(entry) == 4:
            name, face_emb, celeb_gender, celeb_age = entry
            celeb_landmark = None
        else:
            name, face_emb = entry[:2]
            celeb_landmark = None
            celeb_gender, celeb_age = 0, 0
            
        # 1. Embedding Similarity (60%)
        emb_sim = cosine(face_query, face_emb)
        
        # 2. Landmark Similarity (40%)
        # 1 - Euclidean Distance (Phase 5)
        landmark_sim = 0.0
        if landmark_query is not None and celeb_landmark is not None:
            # Landmark similarity = 1 - Euclidean distance
            # Ensure vectors are numpy arrays for norm calculation
            q_vec = np.array(landmark_query)
            c_vec = np.array(celeb_landmark)
            dist = np.linalg.norm(q_vec - c_vec)
            # Clip dist to ensure similarity stays within reasonable range (0 to 1)
            landmark_sim = max(0.0, 1.0 - dist)
        else:
            # Fallback if landmarks are missing
            landmark_sim = emb_sim

        # 3. Attributes (Pre-filter or small bonus)
        # We use gender as a strong filter: if gender doesn't match, penalize heavily
        gender_match = 1.0 if user_gender == celeb_gender else 0.0
        
        # Final Score calculation
        # Base score from Embedding and Landmarks
        base_score = (0.6 * emb_sim) + (0.4 * landmark_sim)
        
        # Apply gender penalty/filter
        final_score = base_score * (0.8 + 0.2 * gender_match)
            
        scores.append((name, final_score))
    
    return sorted(scores, key=lambda x: x[1], reverse=True)[:k]
