import os
import cv2
from tqdm import tqdm

def clean_dataset(raw_path="data/raw"):
    """
    Iterates through the dataset and re-saves images to fix corrupt metadata 
    (e.g., 'Corrupt JPEG data' or 'libpng warning: sBIT: bad length').
    """
    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} not found.")
        return

    categories = ['actors', 'cartoons']
    for cat in categories:
        cat_path = os.path.join(raw_path, cat)
        if not os.path.exists(cat_path): continue
        
        folders = [f for f in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, f))]
        print(f"Cleaning {cat} category...")

        for person_name in tqdm(folders):
            person_dir = os.path.join(cat_path, person_name)
            for img_name in os.listdir(person_dir):
                if not img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    continue
                    
                img_path = os.path.join(person_dir, img_name)
                # Load and re-save
                try:
                    img = cv2.imread(img_path)
                    if img is not None:
                        # Re-saving with OpenCV cleans metadata
                        cv2.imwrite(img_path, img)
                except Exception as e:
                    print(f"Failed to clean {img_path}: {e}")

if __name__ == "__main__":
    clean_dataset()
