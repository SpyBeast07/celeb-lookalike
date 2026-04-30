import cv2
import numpy as np
import mediapipe as mp
from insightface.app import FaceAnalysis

class NewFaceEngine:
    def __init__(self):
        # Initialize MediaPipe Face Mesh
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        
        # Initialize InsightFace
        # buffalo_l is the high-accuracy model
        self.app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_size=(640, 640))

    def get_faces(self, frame):
        """Detect faces and extract embeddings + mediapipe landmarks."""
        # 1. InsightFace Detections & Embeddings
        faces = self.app.get(frame)
        
        if not faces:
            return []
            
        # 2. Add MediaPipe landmarks to each face
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mesh_results = self.face_mesh.process(rgb_frame)
        
        # For simplicity, if multiple faces, we might need a way to match MP landmarks to InsightFace faces
        # But usually we focus on the largest/first face
        if mesh_results.multi_face_landmarks:
            landmarks = mesh_results.multi_face_landmarks[0]
            faces[0].mp_landmarks = landmarks
            faces[0].landmark_vector = self._compute_landmark_features(landmarks)
            
        return faces

    def _compute_landmark_features(self, landmarks):
        """Extract geometric features from 468 landmarks."""
        def get_pt(idx):
            p = landmarks.landmark[idx]
            return np.array([p.x, p.y, p.z])

        # 1. Face Ratio (Width / Height)
        # Width: 454 to 234, Height: 10 to 152
        w = np.linalg.norm(get_pt(454) - get_pt(234))
        h = np.linalg.norm(get_pt(152) - get_pt(10))
        face_ratio = w / h if h != 0 else 1.0

        # 2. Eye Distance (Distance / Face Width)
        # 33 (Right) and 263 (Left)
        eye_dist = np.linalg.norm(get_pt(263) - get_pt(33)) / w if w != 0 else 0.5

        # 3. Nose Length (Nose / Face Height)
        # 168 (Bridge) and 2 (Tip)
        nose_len = np.linalg.norm(get_pt(2) - get_pt(168)) / h if h != 0 else 0.3

        # 4. Jaw Angle (Angle at Chin)
        # 58 (Left Jaw), 152 (Chin), 288 (Right Jaw)
        a = get_pt(58)
        b = get_pt(152) # Chin vertex
        c = get_pt(288)
        
        ba = a - b
        bc = c - b
        
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        jaw_angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        # Normalize jaw angle to 0-1 range (approx 0 to 180 deg)
        jaw_angle_norm = jaw_angle / np.pi

        return [
            float(face_ratio),
            float(eye_dist),
            float(nose_len),
            float(jaw_angle_norm)
        ]

# Create a singleton instance for global use
engine = NewFaceEngine()

def get_faces(frame):
    return engine.get_faces(frame)
