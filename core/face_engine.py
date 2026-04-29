from insightface.app import FaceAnalysis

# Initialize InsightFace with CoreML for Mac optimization
app = FaceAnalysis(providers=['CoreMLExecutionProvider', 'CPUExecutionProvider'])
app.prepare(ctx_id=0)

def get_faces(frame):
    """Detect and extract embeddings from faces in a frame."""
    return app.get(frame)
