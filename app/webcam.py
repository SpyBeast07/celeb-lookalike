import cv2
import numpy as np
from core.face_engine import FaceEngine
from core.database import Database
from core.matcher import Matcher

def start_webcam():
    print("Loading engines and database...")
    engine = FaceEngine()
    db = Database()
    data = db.load()
    
    if data is None:
        print("Error: Database not found. Please run scripts/build_db.py first.")
        return
        
    matcher = Matcher(data['embeddings'], data['labels'])
    
    cap = cv2.VideoCapture(0)
    print("Webcam started. Press 'q' to quit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        faces = engine.detect_and_embed(frame)
        
        for face in faces:
            # Draw bbox
            bbox = face.bbox.astype(int)
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
            
            # Match
            label, score = matcher.find_best_match(face.normed_embedding)
            
            # Display label
            text = f"{label} ({score:.2f})"
            cv2.putText(frame, text, (bbox[0], bbox[1] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.imshow('Celeb Lookalike', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_webcam()
