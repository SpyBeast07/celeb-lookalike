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
            # Match landmarks to faces based on bbox overlap if multiple faces exist
            # For now, let's just attach the first set of landmarks to the first face for basic functionality
            faces[0].mp_landmarks = mesh_results.multi_face_landmarks[0]
            
        return faces

# Create a singleton instance for global use
engine = NewFaceEngine()

def get_faces(frame):
    return engine.get_faces(frame)
