import numpy as np

def cosine(a, b):
    """Calculate cosine similarity between two embeddings."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0
    return np.dot(a, b) / (norm_a * norm_b)

def find_match(face_query, user_gender, user_age, db, k=5):
    """
    Find top K matches in the database.
    Updated to prioritize Face embeddings as CLIP is being deprecated for stability.
    """
    scores = []
    for entry in db:
        # entry format could be: (name, face_emb, clip_emb, gender, age) 
        # or (name, face_emb, gender, age)
        
        if len(entry) == 5:
            name, face_emb, clip_emb, celeb_gender, celeb_age = entry
        elif len(entry) == 4:
            name, face_emb, celeb_gender, celeb_age = entry
            clip_emb = None
        else:
            name, face_emb = entry[:2]
            celeb_gender, celeb_age = 0, 0 # Default fallback
            
        # 1. Face Similarity Score (Primary)
        face_score = cosine(face_query, face_emb)
        
        # 2. Attribute Scores
        # Gender match (1.0 if same, 0.0 if different)
        gender_score = 1.0 if user_gender == celeb_gender else 0.0
        
        # Age similarity (1.0 if same, 0.0 if 50+ years apart)
        age_diff = abs(user_age - celeb_age)
        age_score = 1.0 - (min(age_diff, 50) / 50.0)
        
        # Combined Attribute Score
        attr_score = (0.8 * gender_score) + (0.2 * age_score)
        
        # 3. Final Combined Weighted Score
        # 80% Face + 20% Attributes (since CLIP is removed)
        final_score = (0.8 * face_score) + (0.2 * attr_score)
            
        scores.append((name, final_score))
    
    # Sort by similarity score descending
    return sorted(scores, key=lambda x: x[1], reverse=True)[:k]
