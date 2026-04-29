import os
import cv2
from tqdm import tqdm
from core.face_engine import get_faces
from core.clip_engine import get_clip_embedding
from core.database import save_db

def build_database(raw_path="data/raw"):
    """
    Extracts both InsightFace and CLIP embeddings for each celebrity image.
    Saves format: (name, face_embedding, clip_embedding)
    """
    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} directory not found.")
        return

    db = []
    folders = [f for f in os.listdir(raw_path) if os.path.isdir(os.path.join(raw_path, f))]
    
    print(f"Phase 2: Building database with Face + CLIP embeddings...")
    
    for person_name in tqdm(folders):
        person_dir = os.path.join(raw_path, person_name)
        
        for img_name in os.listdir(person_dir):
            if not img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            img_path = os.path.join(person_dir, img_name)
            img = cv2.imread(img_path)
            if img is None:
                continue
            
            # 1. Extract Face Embedding
            faces = get_faces(img)
            if faces:
                face_emb = faces[0].embedding
                
                # 2. Extract CLIP Embedding (Vibe/Aesthetics)
                # We can use the whole image or the face crop. 
                # Usually CLIP on the whole image captures 'vibe' better.
                clip_emb = get_clip_embedding(img)
                
                # Store in Phase 2 format
                db.append((person_name, face_emb, clip_emb))
    
    if db:
        save_db(db)
        print(f"Successfully built Phase 2 database with {len(db)} entries.")
    else:
        print("No faces detected. Database not created.")

if __name__ == "__main__":
    build_database()
