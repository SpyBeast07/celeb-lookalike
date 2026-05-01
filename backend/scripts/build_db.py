import os
import cv2
import numpy as np
from tqdm import tqdm
from core.face_engine import get_faces
from core.database import save_db

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_RAW_PATH = os.path.join(BASE_DIR, "data", "raw")

def build_database(raw_path=DEFAULT_RAW_PATH):
    """
    Phase 9: Separate Pipelines (Actors vs Cartoons)
    Builds a unified database with category tags.
    """
    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} directory not found.")
        return

    final_db = []
    categories = ['actors', 'cartoons']
    
    for cat in categories:
        cat_path = os.path.join(raw_path, cat)
        if not os.path.exists(cat_path): continue
        
        folders = [f for f in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, f))]
        print(f"Processing {cat} category: {len(folders)} celebrities...")

        for person_name in tqdm(folders):
            person_dir = os.path.join(cat_path, person_name)
            faces_embeddings = []
            landmarks_vectors = []
            genders = []
            ages = []
            
            for img_name in os.listdir(person_dir):
                if not img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    continue
                    
                img_path = os.path.join(person_dir, img_name)
                img = cv2.imread(img_path)
                if img is None: continue
                
                faces = get_faces(img)
                if faces:
                    face = faces[0]
                    faces_embeddings.append(face.embedding)
                    if hasattr(face, 'landmark_vector'):
                        landmarks_vectors.append(face.landmark_vector)
                    genders.append(face.gender)
                    ages.append(face.age)

            if not faces_embeddings: continue
            
            # Calculate Centroids
            avg_face = np.mean(faces_embeddings, axis=0)
            avg_face /= np.linalg.norm(avg_face)
            
            avg_landmark = None
            if landmarks_vectors:
                # Ensure all landmark vectors are the same length (4) to avoid inhomogeneous array errors
                valid_landmarks = [v for v in landmarks_vectors if v is not None and len(v) == 4]
                if valid_landmarks:
                    landmarks_array = np.array(valid_landmarks, dtype=np.float32)
                    avg_landmark = np.mean(landmarks_array, axis=0).tolist()
                else:
                    print(f"Warning: No valid landmarks for {person_name}")
                
            avg_gender = int(round(np.mean(genders)))
            avg_age = int(round(np.mean(ages)))
            
            # Entry: (name, face_emb, landmark_vec, gender, age, category)
            final_db.append((person_name, avg_face, avg_landmark, avg_gender, avg_age, cat))

    if final_db:
        save_db(final_db)
        print(f"Successfully built Phase 9 database with {len(final_db)} entries.")
    else:
        print("No faces found. Database not created.")

if __name__ == "__main__":
    build_database()
