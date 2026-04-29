import cv2
import numpy as np
from core.face_engine import get_faces
from core.clip_engine import get_clip_embedding
from core.matcher import find_match
from core.database import load_db

def start_webcam():
    print("Loading Phase 2 Database (Face + CLIP)...")
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
            # We use the current frame (or a crop around the face for better focus)
            clip_emb = get_clip_embedding(frame)
            
            # Phase 2: Combined Matching
            results = find_match(face_emb, clip_emb, db, k=5)
            
            # Debug logging
            print(f"Top 5 Combined matches: {results}")
            
            display_results = results[:3]
            
            # UI Drawing
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
            
            # Corners
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)
            l = 20
            c = (0, 255, 0)
            cv2.line(frame, (x1, y1), (x1+l, y1), c, 3); cv2.line(frame, (x1, y1), (x1, y1+l), c, 3)
            cv2.line(frame, (x2, y1), (x2-l, y1), c, 3); cv2.line(frame, (x2, y1), (x2, y1+l), c, 3)
            cv2.line(frame, (x1, y2), (x1+l, y2), c, 3); cv2.line(frame, (x1, y2), (x1, y2-l), c, 3)
            cv2.line(frame, (x2, y2), (x2-l, y2), c, 3); cv2.line(frame, (x2, y2), (x2, y2-l), c, 3)

            # Overlay
            overlay = frame.copy()
            cv2.rectangle(overlay, (x1, y1-80), (x1+220, y1), (0,0,0), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
            
            for i, (name, score) in enumerate(display_results):
                color = (0, 255, 0) if i == 0 else (255, 255, 255)
                cv2.putText(frame, f"{name}: {int(score*100)}%", 
                            (x1+10, y1-10-i*22), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1, cv2.LINE_AA)
        
        cv2.imshow("Phase 2: Face + CLIP Vibe Matching", frame)
        if cv2.waitKey(1) == 27:
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_webcam()
