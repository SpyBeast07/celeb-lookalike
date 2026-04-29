import cv2
import insightface
from insightface.app import FaceAnalysis

class FaceEngine:
    def __init__(self, model_name='buffalo_l'):
        self.app = FaceAnalysis(name=model_name)
        self.app.prepare(ctx_id=0, det_size=(640, 640))

    def detect_and_embed(self, img):
        faces = self.app.get(img)
        return faces
