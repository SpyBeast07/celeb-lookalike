import os
import cv2
from tqdm import tqdm
from core.face_engine import get_faces
from core.clip_engine import get_clip_embedding
from core.database import save_db

def build_database(raw_path="data/raw"):
    """
    Extracts Face, CLIP, and Human Attributes (Gender/Age) for each celebrity.
    Saves format: (name, face_embedding, clip_embedding, gender, age)
    """
    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} directory not found.")
        return

    db = []
    folders = [f for f in os.listdir(raw_path) if os.path.isdir(os.path.join(raw_path, f))]
    
    print(f"Phase 3: Building database with Face + CLIP + Attributes...")
    
    for person_name in tqdm(folders):
        person_dir = os.path.join(raw_path, person_name)
        
        # We'll average attributes across multiple images of the same person if available
        # or just take the most frequent/average. For simplicity, we'll collect all and average at the end
        # but let's just use the first valid detection for now as per minimal core engine plan.
        
        for img_name in os.listdir(person_dir):
            if not img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            img_path = os.path.join(person_dir, img_name)
            img = cv2.imread(img_path)
            if img is None:
                continue
            
            faces = get_faces(img)
            if faces:
                face = faces[0]
                face_emb = face.embedding
                clip_emb = get_clip_embedding(img)
                
                # Phase 3 Attributes
                gender = face.gender # 0 or 1
                age = face.age
                
                # Store in Phase 3 format
                db.append((person_name, face_emb, clip_emb, gender, age))
                # For now, 1 entry per image is fine, matcher will handle duplicates/averaging
    
    if db:
        save_db(db)
        print(f"Successfully built Phase 3 database with {len(db)} entries.")
    else:
        print("No faces detected. Database not created.")

if __name__ == "__main__":
    build_database()
