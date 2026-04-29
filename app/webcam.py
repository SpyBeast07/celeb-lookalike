import cv2
import numpy as np
from core.face_engine import get_faces
from core.clip_engine import get_clip_embedding
from core.matcher import find_match
from core.database import load_db

def start_webcam():
    print("Loading Phase 3 Database (Face + CLIP + Attributes)...")
    db = load_db()
    if not db:
        print("Error: Database is empty. Please run 'scripts/build_db.py' first.")
        return

    print("Starting webcam... Press ESC to exit.")
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Flip for mirror effect
        frame = cv2.flip(frame, 1)
            
        faces = get_faces(frame)
        for face in faces:
            # 1. Get Face Embedding
            face_emb = face.embedding
            
            # 2. Get CLIP Embedding (Vibe/Aesthetics)
            # Use current frame
            clip_emb = get_clip_embedding(frame)
            
            # 3. Get User Attributes (Phase 3)
            user_gender = face.gender # 0=Female, 1=Male
            user_age = face.age
            
            # Phase 3: Combined Matching with Attribute Filtering
            results = find_match(face_emb, clip_emb, user_gender, user_age, db, k=5)
            
            # Debug logging
            gender_str = "Male" if user_gender == 1 else "Female"
            print(f"User: {gender_str}, Age: {user_age} | Top matches: {results}")
            
            display_results = results[:3]
            
            # UI Drawing
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
            
            # Modern Tech Corners
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)
            l = 20
            c = (0, 255, 0)
            cv2.line(frame, (x1, y1), (x1+l, y1), c, 3); cv2.line(frame, (x1, y1), (x1, y1+l), c, 3)
            cv2.line(frame, (x2, y1), (x2-l, y1), c, 3); cv2.line(frame, (x2, y1), (x2, y1+l), c, 3)
            cv2.line(frame, (x1, y2), (x1+l, y2), c, 3); cv2.line(frame, (x1, y2), (x1, y2-l), c, 3)
            cv2.line(frame, (x2, y2), (x2-l, y2), c, 3); cv2.line(frame, (x2, y2), (x2, y2-l), c, 3)

            # Overlay for names
            overlay = frame.copy()
            cv2.rectangle(overlay, (x1, y1-85), (x1+230, y1), (0,0,0), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
            
            # Display user attributes briefly
            cv2.putText(frame, f"{gender_str}, {int(user_age)}", (x1, y2 + 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            
            for i, (name, score) in enumerate(display_results):
                color = (0, 255, 0) if i == 0 else (255, 255, 255)
                cv2.putText(frame, f"{name}: {int(score*100)}%", 
                            (x1+10, y1-10-i*22), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1, cv2.LINE_AA)
        
        cv2.imshow("Phase 3: Human Perception Matching", frame)
        if cv2.waitKey(1) == 27:
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_webcam()
