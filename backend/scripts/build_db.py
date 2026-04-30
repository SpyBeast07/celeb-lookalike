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
    Build celebrity database using the new engine (InsightFace + MediaPipe).
    Now stores Face Embeddings, Landmark Vectors, and Attributes.
    """
    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} directory not found.")
        return

    celeb_data = {}
    
    folders = [f for f in os.listdir(raw_path) if os.path.isdir(os.path.join(raw_path, f))]
    print(f"Phase 4: Extracting structural landmarks for {len(folders)} celebrities...")

    for person_name in tqdm(folders):
        person_dir = os.path.join(raw_path, person_name)
        celeb_data[person_name] = {'face': [], 'landmark': [], 'gender': [], 'age': []}
        
        for img_name in os.listdir(person_dir):
            if not img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            img_path = os.path.join(person_dir, img_name)
            img = cv2.imread(img_path)
            if img is None: continue
            
            faces = get_faces(img)
            if faces:
                face = faces[0]
                
                # Filter for "large enough" face
                bbox = face.bbox
                if (bbox[2]-bbox[0]) < 80: continue

                celeb_data[person_name]['face'].append(face.embedding)
                if hasattr(face, 'landmark_vector'):
                    celeb_data[person_name]['landmark'].append(face.landmark_vector)
                celeb_data[person_name]['gender'].append(face.gender)
                celeb_data[person_name]['age'].append(face.age)

    # Calculate Centroids
    final_db = []
    for person_name, data in celeb_data.items():
        if not data['face']:
            continue
            
        # 1. Face Centroid
        avg_face = np.mean(data['face'], axis=0)
        avg_face /= np.linalg.norm(avg_face)
        
        # 2. Landmark Centroid (Phase 5: Robust Averaging)
        if data['landmark']:
            # Explicitly convert to numpy array and average to avoid inhomogeneous shape errors
            landmarks_array = np.array(data['landmark'], dtype=np.float32)
            avg_landmark = np.mean(landmarks_array, axis=0).tolist()
        else:
            avg_landmark = None
            
        # 3. Attributes
        avg_gender = int(round(np.mean(data['gender'])))
        avg_age = int(round(np.mean(data['age'])))
        
        # Save entry: (name, face_emb, landmark_vec, gender, age)
        final_db.append((person_name, avg_face, avg_landmark, avg_gender, avg_age))

    if final_db:
        save_db(final_db)
        print(f"Successfully built Phase 4 database for {len(final_db)} celebrities.")
    else:
        print("No faces found. Database not created.")

if __name__ == "__main__":
    build_database()
