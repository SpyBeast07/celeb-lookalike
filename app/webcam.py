import cv2
import numpy as np
from core.face_engine import get_faces
from core.matcher import find_match
from core.database import load_db

def start_webcam():
    print("Loading database...")
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
            
        # Optional: flip frame for mirror effect
        frame = cv2.flip(frame, 1)
            
        faces = get_faces(frame)
        for face in faces:
            emb = face.embedding
            # Phase 1: Top-K Matching (Top 3 results)
            results = find_match(emb, db, k=5) # Get 5 for debug logging
            
            # Phase 0 Debug: Logging Top 5 scores to console
            print(f"Top 5 matches: {results}")
            
            # Phase 1 UI: Display Top 3 on screen
            display_results = results[:3]
            
            # Get face bounding box
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
            
            # Premium UI: Draw modern bounding box
            # Draw main rectangle
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)
            
            # Draw corners for a "tech" look
            length = 20
            color = (0, 255, 0) # Green
            cv2.line(frame, (x1, y1), (x1 + length, y1), color, 3)
            cv2.line(frame, (x1, y1), (x1, y1 + length), color, 3)
            cv2.line(frame, (x2, y1), (x2 - length, y1), color, 3)
            cv2.line(frame, (x2, y1), (x2, y1 + length), color, 3)
            cv2.line(frame, (x1, y2), (x1 + length, y2), color, 3)
            cv2.line(frame, (x1, y2), (x1, y2 - length), color, 3)
            cv2.line(frame, (x2, y2), (x2 - length, y2), color, 3)
            cv2.line(frame, (x2, y2), (x2, y2 - length), color, 3)

            # Display Top-3 results with a semi-transparent background
            overlay = frame.copy()
            bg_height = 80
            cv2.rectangle(overlay, (x1, y1 - bg_height), (x1 + 200, y1), (0, 0, 0), -1)
            alpha = 0.6
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
            
            for i, (name, score) in enumerate(display_results):
                text = f"{name}: {int(score*100)}%"
                # Score-based coloring (Optional)
                text_color = (255, 255, 255)
                if i == 0: text_color = (0, 255, 0) # Top match in green
                
                cv2.putText(frame, text,
                            (x1 + 10, y1 - 10 - i*22),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                            text_color, 1, cv2.LINE_AA)
        
        cv2.imshow("Celebrity Lookalike Cam - Phase 1", frame)
        if cv2.waitKey(1) == 27: # ESC key
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_webcam()
