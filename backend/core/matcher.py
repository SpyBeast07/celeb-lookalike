import numpy as np

def cosine(a, b):
    """Calculate cosine similarity between two embeddings."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0
    return np.dot(a, b) / (norm_a * norm_b)

def find_match(face_query, clip_query, user_gender, user_age, db, k=3):
    """
    Find top K matches in the database using Face, CLIP, and Attribute scores.
    db entry: (name, face_emb, clip_emb, gender, age)
    """
    scores = []
    for entry in db:
        # Support Phase 3 format (name, face_emb, clip_emb, gender, age)
        if len(entry) == 5:
            name, face_emb, clip_emb, celeb_gender, celeb_age = entry
            
            # 1. Similarity Scores
            face_score = cosine(face_query, face_emb)
            clip_score = cosine(clip_query, clip_emb)
            
            # 2. Attribute Scores (Phase 3)
            # Gender match (1.0 if same, 0.0 if different)
            gender_score = 1.0 if user_gender == celeb_gender else 0.0
            
            # Age similarity (1.0 if same, 0.0 if 50+ years apart)
            age_diff = abs(user_age - celeb_age)
            age_score = 1.0 - (min(age_diff, 50) / 50.0)
            
            # Combined Attribute Score
            # We give more weight to gender to avoid "dumb" matches
            attr_score = (0.7 * gender_score) + (0.3 * age_score)
            
            # 3. Final Combined Weighted Score
            # 40% Face + 40% CLIP + 20% Attributes
            final_score = (0.4 * face_score) + (0.4 * clip_score) + (0.2 * attr_score)
            
        elif len(entry) == 3: # Phase 2 format
            name, face_emb, clip_emb = entry
            face_score = cosine(face_query, face_emb)
            clip_score = cosine(clip_query, clip_emb)
            final_score = (0.5 * face_score) + (0.5 * clip_score)
        else: # Phase 0/1 format
            name, face_emb = entry
            final_score = cosine(face_query, face_emb)
            
        scores.append((name, final_score))
    
    # Sort by similarity score descending
    return sorted(scores, key=lambda x: x[1], reverse=True)[:k]
