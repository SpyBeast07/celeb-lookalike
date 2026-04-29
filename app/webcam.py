import cv2
import numpy as np
from collections import deque
from core.face_engine import get_faces
from core.clip_engine import get_clip_embedding
from core.matcher import find_match
from core.database import load_db

# Phase 4: Temporal Smoothing Buffer
# This stops labels from flickering by averaging results over the last 10 frames
history = deque(maxlen=10)

def average_scores(history_buffer):
    """
    Combines and averages scores from the last N frames to stabilize results.
    """
    if not history_buffer:
        return []
    
    combined_scores = {}
    # Count how many frames each celebrity has appeared in
    counts = {}
    
    for frame_results in history_buffer:
        for name, score in frame_results:
            combined_scores[name] = combined_scores.get(name, 0) + score
            counts[name] = counts.get(name, 0) + 1
            
    # Calculate average score for each person
    # Note: We divide by the total number of frames in history to penalize 
    # candidates that only appear sporadically.
    num_frames = len(history_buffer)
    avg_results = []
    for name, total_score in combined_scores.items():
        avg_results.append((name, total_score / num_frames))
        
    # Sort by average score descending
    return sorted(avg_results, key=lambda x: x[1], reverse=True)

def start_webcam():
    print("Loading Phase 3 Database (Face + CLIP + Attributes)...")
    db = load_db()
    if not db:
        print("Error: Database is empty. Please run 'scripts/build_db.py' first.")
        return

    print("Starting Phase 4: Temporal Smoothing... Press ESC to exit.")
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Flip for mirror effect
        frame = cv2.flip(frame, 1)
            
        faces = get_faces(frame)
        
        # If no faces detected, we can either clear history or keep it.
        # Clearing it makes the response faster when a new face appears.
        if not faces:
            history.clear()
        
        for face in faces:
            # 1. Get Face Embedding
            face_emb = face.embedding
            
            # 2. Get CLIP Embedding
            clip_emb = get_clip_embedding(frame)
            
            # 3. Get User Attributes
            user_gender = face.gender 
            user_age = face.age
            
            # Match against database
            current_results = find_match(face_emb, clip_emb, user_gender, user_age, db, k=5)
            
            # Phase 4: Update history and average
            history.append(current_results)
            smoothed_results = average_scores(history)
            
            # Debug logging
            print(f"Smoothed Top Match: {smoothed_results[0] if smoothed_results else 'None'}")
            
            display_results = smoothed_results[:3]
            
            # UI Drawing
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
            
            # Corners
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)
            l = 20; c = (0, 255, 0)
            cv2.line(frame, (x1, y1), (x1+l, y1), c, 3); cv2.line(frame, (x1, y1), (x1, y1+l), c, 3)
            cv2.line(frame, (x2, y1), (x2-l, y1), c, 3); cv2.line(frame, (x2, y1), (x2, y1+l), c, 3)
            cv2.line(frame, (x1, y2), (x1+l, y2), c, 3); cv2.line(frame, (x1, y2), (x1, y2-l), c, 3)
            cv2.line(frame, (x2, y2), (x2-l, y2), c, 3); cv2.line(frame, (x2, y2), (x2, y2-l), c, 3)

            # Overlay
            overlay = frame.copy()
            cv2.rectangle(overlay, (x1, y1-85), (x1+230, y1), (0,0,0), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
            
            gender_str = "Male" if user_gender == 1 else "Female"
            cv2.putText(frame, f"{gender_str}, {int(user_age)}", (x1, y2 + 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            
            for i, (name, score) in enumerate(display_results):
                color = (0, 255, 0) if i == 0 else (255, 255, 255)
                cv2.putText(frame, f"{name}: {int(score*100)}%", 
                            (x1+10, y1-10-i*22), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1, cv2.LINE_AA)
        
        cv2.imshow("Phase 4: Stable Lookalike Cam", frame)
        if cv2.waitKey(1) == 27:
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_webcam()
