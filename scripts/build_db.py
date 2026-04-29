import os
import cv2
import numpy as np
from tqdm import tqdm
from core.face_engine import get_faces
from core.clip_engine import get_clip_embedding
from core.database import save_db

def build_database(raw_path="data/raw"):
    """
    Phase 7 Upgrade: Cluster embeddings per celebrity.
    Instead of multiple entries, we store one 'Centroid' embedding per celeb.
    Filters for frontal faces and averages attributes for high-quality matching.
    """
    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} directory not found.")
        return

    # Dictionary to aggregate data per person
    # { person_name: { 'face_embs': [], 'clip_embs': [], 'genders': [], 'ages': [] } }
    celeb_data = {}
    
    folders = [f for f in os.listdir(raw_path) if os.path.isdir(os.path.join(raw_path, f))]
    print(f"Phase 7: Upgrading dataset. Processing {len(folders)} celebrities...")

    for person_name in tqdm(folders):
        person_dir = os.path.join(raw_path, person_name)
        celeb_data[person_name] = {'face': [], 'clip': [], 'gender': [], 'age': []}
        
        for img_name in os.listdir(person_dir):
            if not img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            img_path = os.path.join(person_dir, img_name)
            img = cv2.imread(img_path)
            if img is None: continue
            
            faces = get_faces(img)
            if faces:
                # Filter for High Quality: Large faces and frontal pose
                # InsightFace pose is (pitch, yaw, roll)
                face = faces[0]
                pose = getattr(face, 'pose', [0,0,0])
                
                # Simple frontal check: absolute yaw/pitch/roll should be small
                if any(abs(p) > 25 for p in pose): 
                    # Skip profile or extreme angles for cleaner dataset
                    continue
                
                # Check for "large enough" face to avoid blurry small detections
                bbox = face.bbox
                if (bbox[2]-bbox[0]) < 80: continue

                celeb_data[person_name]['face'].append(face.embedding)
                celeb_data[person_name]['clip'].append(get_clip_embedding(img))
                celeb_data[person_name]['gender'].append(face.gender)
                celeb_data[person_name]['age'].append(face.age)

    # 2. Cluster & Centroid Calculation
    final_db = []
    for person_name, data in celeb_data.items():
        if not data['face']:
            continue
            
        # Calculate mean Face and CLIP embeddings (Centroids)
        # We normalize again after averaging to keep them on the unit hypersphere
        avg_face = np.mean(data['face'], axis=0)
        avg_face /= np.linalg.norm(avg_face)
        
        avg_clip = np.mean(data['clip'], axis=0)
        avg_clip /= np.linalg.norm(avg_clip)
        
        # Most frequent gender (Mode)
        avg_gender = round(np.mean(data['gender']))
        
        # Average age
        avg_age = np.mean(data['age'])
        
        # Save as a single robust entry for this celebrity
        final_db.append((person_name, avg_face, avg_clip, avg_gender, avg_age))

    if final_db:
        save_db(final_db)
        print(f"Successfully upgraded database! Created centroids for {len(final_db)} celebrities.")
        print(f"Total entries reduced from images -> celebrities for faster matching.")
    else:
        print("No high-quality frontal faces found. Database not created.")

if __name__ == "__main__":
    build_database()
