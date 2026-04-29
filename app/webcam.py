import cv2
import numpy as np
from collections import deque
from core.face_engine import get_faces
from core.clip_engine import get_clip_embedding
from core.matcher import find_match
from core.database import load_db

class FaceTracker:
    """
    Simple Centroid Tracker to maintain identity across frames.
    """
    def __init__(self, max_disappear=10):
        self.next_id = 0
        self.tracked_faces = {} # {id: (centroid, bbox)}
        self.disappeared = {}   # {id: frame_count}
        self.max_disappear = max_disappear

    def update(self, detections):
        # detections is a list of Face objects from InsightFace
        if not detections:
            for fid in list(self.disappeared.keys()):
                self.disappeared[fid] += 1
                if self.disappeared[fid] > self.max_disappear:
                    self.deregister(fid)
            return []

        # Calculate centroids for current frame
        current_centroids = []
        for face in detections:
            bbox = face.bbox.astype(int)
            cx, cy = (bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2
            current_centroids.append((cx, cy))

        if not self.tracked_faces:
            for i in range(len(current_centroids)):
                self.register(current_centroids[i], detections[i])
        else:
            fids = list(self.tracked_faces.keys())
            old_centroids = [c for c, b in self.tracked_faces.values()]

            # Compute distances between old and new centroids
            # D[i, j] is distance between old_centroid[i] and current_centroid[j]
            D = np.zeros((len(old_centroids), len(current_centroids)))
            for i, oc in enumerate(old_centroids):
                for j, nc in enumerate(current_centroids):
                    D[i, j] = np.linalg.norm(np.array(oc) - np.array(nc))

            # Match greedily
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]
            used_rows, used_cols = set(), set()

            for r, c in zip(rows, cols):
                if r in used_rows or c in used_cols: continue
                if D[r, c] > 100: continue # Don't match if too far

                fid = fids[r]
                self.tracked_faces[fid] = (current_centroids[c], detections[c])
                self.disappeared[fid] = 0
                used_rows.add(r)
                used_cols.add(c)

            # Register new faces
            for i in range(len(current_centroids)):
                if i not in used_cols:
                    self.register(current_centroids[i], detections[i])

            # Mark old faces as disappeared
            for i in range(len(fids)):
                if i not in used_rows:
                    fid = fids[i]
                    self.disappeared[fid] += 1
                    if self.disappeared[fid] > self.max_disappear:
                        self.deregister(fid)

        # Return list of (id, face_obj)
        results = []
        for fid, (centroid, face_obj) in self.tracked_faces.items():
            if self.disappeared[fid] == 0:
                results.append((fid, face_obj))
        return results

    def register(self, centroid, face_obj):
        self.tracked_faces[self.next_id] = (centroid, face_obj)
        self.disappeared[self.next_id] = 0
        self.next_id += 1

    def deregister(self, fid):
        if fid in self.tracked_faces:
            del self.tracked_faces[fid]
            del self.disappeared[fid]
            # Also clear history from global scope if needed
            if fid in face_histories:
                del face_histories[fid]

# Global histories for each tracked face ID
face_histories = {} # {face_id: deque(maxlen=10)}

def average_scores(history_buffer):
    if not history_buffer: return []
    combined = {}
    for res in history_buffer:
        for name, score in res:
            combined[name] = combined.get(name, 0) + score
    avg = [(n, s / len(history_buffer)) for n, s in combined.items()]
    return sorted(avg, key=lambda x: x[1], reverse=True)

def start_webcam():
    print("Loading Phase 3 Database...")
    db = load_db()
    if not db: return

    print("Starting Phase 5: Multi-Face Tracking... Press ESC to exit.")
    tracker = FaceTracker()
    face_frames_counter = {} # Tracking frame count per face for optimization
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
            
        detections = get_faces(frame)
        tracked_results = tracker.update(detections)
        
        for face_id, face in tracked_results:
            # Phase 5 Optimization: Skip expensive CLIP/Matching every frame
            # Only update every 5 frames per person to save CPU/GPU
            if face_id not in face_frames_counter:
                face_frames_counter[face_id] = 0
            
            if face_frames_counter[face_id] % 5 == 0:
                # 1. Embeddings
                face_emb = face.embedding
                clip_emb = get_clip_embedding(frame)
                
                # 2. Match
                current_matches = find_match(face_emb, clip_emb, face.gender, face.age, db, k=5)
                
                # 3. Tracked History
                if face_id not in face_histories:
                    face_histories[face_id] = deque(maxlen=10)
                
                face_histories[face_id].append(current_matches)
                
            face_frames_counter[face_id] += 1
            
            # Use the latest smoothed results
            smoothed = average_scores(face_histories.get(face_id, []))
            if not smoothed: continue
            
            # 4. UI Drawing
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
            
            # Tech Box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)
            l=20; c=(0, 255, 0)
            for p1, p2 in [((x1,y1),(x1+l,y1)), ((x1,y1),(x1,y1+l)), ((x2,y1),(x2-l,y1)), ((x2,y1),(x2,y1+l)), 
                           ((x1,y2),(x1+l,y2)), ((x1,y2),(x1,y2-l)), ((x2,y2),(x2-l,y2)), ((x2,y2),(x2,y2-l))]:
                cv2.line(frame, p1, p2, c, 3)

            # Identity ID Tag
            cv2.putText(frame, f"ID:{face_id}", (x1, y1-95), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,255,0), 1)

            # Overlay
            overlay = frame.copy()
            cv2.rectangle(overlay, (x1, y1-85), (x1+230, y1), (0,0,0), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
            
            gender_str = "Male" if face.gender == 1 else "Female"
            cv2.putText(frame, f"{gender_str}, {int(face.age)}", (x1, y2 + 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            
            for i, (name, score) in enumerate(smoothed[:3]):
                color = (0, 255, 0) if i == 0 else (255, 255, 255)
                cv2.putText(frame, f"{name}: {int(score*100)}%", 
                            (x1+10, y1-10-i*22), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1, cv2.LINE_AA)
        
        cv2.imshow("Phase 5: Pro-Level Face Tracking", frame)
        if cv2.waitKey(1) == 27: break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_webcam()
