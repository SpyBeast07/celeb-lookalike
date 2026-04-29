import os
import cv2
from tqdm import tqdm
from core.face_engine import get_faces
from core.database import save_db

def build_database(raw_path="data/raw"):
    """
    Reads images from the raw dataset, extracts face embeddings, 
    and saves them to a database file.
    """
    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} directory not found.")
        return

    db = []
    
    # Iterate through folders (each folder name is the celebrity's name)
    folders = [f for f in os.listdir(raw_path) if os.path.isdir(os.path.join(raw_path, f))]
    
    print(f"Found {len(folders)} celebrity folders. Starting embedding extraction...")
    
    for person_name in tqdm(folders):
        person_dir = os.path.join(raw_path, person_name)
        
        for img_name in os.listdir(person_dir):
            if not img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            img_path = os.path.join(person_dir, img_name)
            img = cv2.imread(img_path)
            if img is None:
                continue
            
            faces = get_faces(img)
            if faces:
                # We take the first (usually most prominent) face detected
                emb = faces[0].embedding
                db.append((person_name, emb))
    
    if db:
        save_db(db)
        print(f"Successfully built database with {len(db)} embeddings.")
    else:
        print("No faces detected in the dataset. Database not created.")

if __name__ == "__main__":
    build_database()
