import os
import cv2
import numpy as np
from tqdm import tqdm
from core.face_engine import FaceEngine
from core.database import Database

def build_database(raw_data_path):
    print(f"Building database from {raw_data_path}...")
    engine = FaceEngine()
    db = Database()
    
    embeddings = []
    labels = []
    
    # Iterate through folders (celebrities)
    for person_name in tqdm(os.listdir(raw_data_path)):
        person_dir = os.path.join(raw_data_path, person_name)
        if not os.path.isdir(person_dir):
            continue
            
        # Iterate through images for each person
        for img_name in os.listdir(person_dir):
            img_path = os.path.join(person_dir, img_name)
            if not img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            img = cv2.imread(img_path)
            if img is None:
                print(f"Warning: Could not read {img_path}")
                continue
                
            faces = engine.detect_and_embed(img)
            
            if not faces:
                # print(f"Warning: No face detected in {img_path}")
                continue
                
            # Use the largest face or first detected face
            # InsightFace sorts by detection score, but we could sort by bbox size
            face = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]
            
            embeddings.append(face.normed_embedding)
            labels.append(person_name)
            
    if embeddings:
        print(f"Saving {len(embeddings)} embeddings to database...")
        db.save(np.array(embeddings), labels)
        print("Done!")
    else:
        print("No embeddings found to save.")

if __name__ == "__main__":
    # Example usage: point to the raw data directory
    # Note: You can symlink or move your celebrities_small folder to data/raw
    build_database('data/raw')
