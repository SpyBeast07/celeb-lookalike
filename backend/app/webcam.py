import cv2
import numpy as np
from collections import deque
from core.face_engine import get_faces
from core.matcher import find_match
from core.database import load_db

class FaceTracker:
    def __init__(self, max_disappear=15):
        self.next_id = 0
        self.tracked_faces = {} # {id: (centroid, face_obj)}
        self.disappeared = {}
        self.max_disappear = max_disappear
        self.smoothed_bboxes = {} # {id: bbox} for smooth transitions

    def update(self, detections):
        if not detections:
            for fid in list(self.disappeared.keys()):
                self.disappeared[fid] += 1
                if self.disappeared[fid] > self.max_disappear:
                    self.deregister(fid)
            return []

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

            D = np.zeros((len(old_centroids), len(current_centroids)))
            for i, oc in enumerate(old_centroids):
                for j, nc in enumerate(current_centroids):
                    D[i, j] = np.linalg.norm(np.array(oc) - np.array(nc))

            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]
            used_rows, used_cols = set(), set()

            for r, c in zip(rows, cols):
                if r in used_rows or c in used_cols: continue
                if D[r, c] > 150: continue

                fid = fids[r]
                # Smooth bbox transition
                old_bbox = self.tracked_faces[fid][1].bbox if self.tracked_faces[fid][1] is not None else detections[c].bbox
                alpha = 0.3 # Smoothing factor
                smoothed_bbox = alpha * detections[c].bbox + (1 - alpha) * old_bbox
                detections[c].bbox = smoothed_bbox
                
                self.tracked_faces[fid] = (current_centroids[c], detections[c])
                self.disappeared[fid] = 0
                used_rows.add(r)
                used_cols.add(c)

            for i in range(len(current_centroids)):
                if i not in used_cols:
                    self.register(current_centroids[i], detections[i])

            for i in range(len(fids)):
                if i not in used_rows:
                    fid = fids[i]
                    self.disappeared[fid] += 1
                    if self.disappeared[fid] > self.max_disappear:
                        self.deregister(fid)

        return [(fid, face) for fid, (c, face) in self.tracked_faces.items() if self.disappeared[fid] == 0]

    def register(self, centroid, face_obj):
        self.tracked_faces[self.next_id] = (centroid, face_obj)
        self.disappeared[self.next_id] = 0
        self.next_id += 1

    def deregister(self, fid):
        if fid in self.tracked_faces:
            del self.tracked_faces[fid]
            del self.disappeared[fid]
            if fid in face_histories: del face_histories[fid]

face_histories = {} 

def average_scores(history_buffer):
    if not history_buffer: return []
    combined = {}
    for res in history_buffer:
        for name, score in res:
            combined[name] = combined.get(name, 0) + score
    avg = [(n, s / len(history_buffer)) for n, s in combined.items()]
    return sorted(avg, key=lambda x: x[1], reverse=True)

def draw_premium_ui(frame, x1, y1, x2, y2, face_id, gender_str, age, results):
    # 1. Tech Bounding Box
    color = (0, 255, 0) if results[0][1] > 0.4 else (0, 200, 255)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)
    l = 25
    for p1, p2 in [((x1,y1),(x1+l,y1)), ((x1,y1),(x1,y1+l)), ((x2,y1),(x2-l,y1)), ((x2,y1),(x2,y1+l)), 
                   ((x1,y2),(x1+l,y2)), ((x1,y2),(x1,y2-l)), ((x2,y2),(x2-l,y2)), ((x2,y2),(x2,y2-l))]:
        cv2.line(frame, p1, p2, color, 3)

    # 2. Match Banner
    main_match, main_score = results[0]
    banner_text = f"HOT MATCH: {main_match}" if main_score > 0.45 else f"LOOKS LIKE: {main_match}"
    
    # Header Overlay
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1 - 100), (x1 + 250, y1), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    
    cv2.putText(frame, banner_text, (x1 + 5, y1 - 75), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

    # 3. Confidence Bars
    for i, (name, score) in enumerate(results[:3]):
        bar_x = x1 + 5
        bar_y = y1 - 55 + i*18
        bar_w = 120
        bar_h = 8
        
        # Draw Name
        cv2.putText(frame, f"{name[:15]}", (bar_x, bar_y + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1, cv2.LINE_AA)
        
        # Draw Bar Background
        cv2.rectangle(frame, (bar_x + 100, bar_y), (bar_x + 100 + bar_w, bar_y + bar_h), (50, 50, 50), -1)
        
        # Draw Progress
        progress = int(bar_w * score)
        bar_color = (0, 255, 0) if i == 0 else (0, 200, 255)
        cv2.rectangle(frame, (bar_x + 100, bar_y), (bar_x + 100 + progress, bar_y + bar_h), bar_color, -1)
        
        # Draw %
        cv2.putText(frame, f"{int(score*100)}%", (bar_x + 100 + bar_w + 5, bar_y + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    # 4. User Meta
    cv2.putText(frame, f"{gender_str} | {int(age)}y", (x1, y2 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

def start_webcam():
    print("Starting New Engine Webcam experience (InsightFace + MediaPipe)...")
    db = load_db()
    if not db: 
        print("Error: No database found. Run --build first.")
        return

    tracker = FaceTracker()
    face_frames_counter = {}
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        
        detections = get_faces(frame)
        tracked_results = tracker.update(detections)
        
        for face_id, face in tracked_results:
            if face_id not in face_frames_counter: face_frames_counter[face_id] = 0
            
            # Matching logic (No CLIP)
            if face_frames_counter[face_id] % 4 == 0:
                face_histories.setdefault(face_id, deque(maxlen=10)).append(
                    find_match(face.embedding, face.gender, face.age, db, k=5)
                )
            face_frames_counter[face_id] += 1
            
            smoothed = average_scores(face_histories.get(face_id, []))
            if not smoothed: continue
            
            bbox = face.bbox.astype(int)
            draw_premium_ui(frame, bbox[0], bbox[1], bbox[2], bbox[3], face_id, 
                            "Male" if face.gender == 1 else "Female", face.age, smoothed)
        
        cv2.imshow("SpyBeast07 Celeb Lookalike - New Engine", frame)
        if cv2.waitKey(1) == 27: break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_webcam()
