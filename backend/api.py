import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from core.face_engine import get_faces
from core.matcher import find_match
from core.database import load_db
import io
import time
from collections import deque

app = FastAPI(title="Celeb Lookalike API - New Engine")

# --- Multi-frame Aggregation State ---
# Stores recent embeddings/landmarks per client IP to smooth results
aggregation_buffers = {}
BUFFER_MAX = 5
BUFFER_TIMEOUT = 10.0 # Seconds before resetting buffer

# Configure CORS for Svelte frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global database variable
db = None

@app.on_event("startup")
async def startup_event():
    global db
    print("Loading celebrity database...")
    db = load_db()
    if not db:
        print("Warning: Database not found. Please run with --build first.")

@app.get("/")
async def root():
    return {"message": "Celeb Lookalike API is running with new engine (InsightFace + MediaPipe)"}

@app.post("/analyze")
async def analyze_face(file: UploadFile = File(...), request: Request = None, category: str = None):
    """
    Follows Architecture:
    Detection -> Alignment -> Embedding -> Landmarks -> Feature Extraction 
    -> Multi-frame aggregation -> Hybrid similarity scoring -> Top-K
    """
    if not db:
        return {"error": "Database not loaded. Run --build first."}

    # 1. INPUT IMAGE
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if frame is None:
        return {"error": "Invalid image format"}

    # 2, 3, 4, 5. Face Detection, Alignment, Embedding (ArcFace), Landmarks (MediaPipe)
    detections = get_faces(frame)
    
    if not detections:
        return {"results": [], "count": 0}

    # Simplified Multi-frame aggregation logic (keyed by IP for the web session)
    client_ip = request.client.host if request and request.client else "unknown"
    now = time.time()
    
    results = []
    for face in detections:
        # 6. Feature Extraction (Landmarks Vector)
        landmark_vector = getattr(face, 'landmark_vector', None)
        
        # 7. Multi-frame aggregation
        # If this is a sequence of "Find Match" clicks, we aggregate features
        if client_ip not in aggregation_buffers or (now - aggregation_buffers[client_ip]['last_seen'] > BUFFER_TIMEOUT):
            aggregation_buffers[client_ip] = {'emb': deque(maxlen=BUFFER_MAX), 'landmark': deque(maxlen=BUFFER_MAX)}
        
        buf = aggregation_buffers[client_ip]
        buf['emb'].append(face.embedding)
        if landmark_vector:
            buf['landmark'].append(landmark_vector)
        aggregation_buffers[client_ip]['last_seen'] = now
        
        # Calculate aggregated features
        agg_embedding = np.mean(buf['emb'], axis=0)
        agg_embedding /= np.linalg.norm(agg_embedding)
        
        agg_landmark = None
        if buf['landmark']:
            agg_landmark = np.mean(buf['landmark'], axis=0).tolist()

        # 8. Hybrid similarity scoring (Face + Landmarks + Attributes)
        matches = find_match(
            agg_embedding, 
            face.gender, 
            face.age, 
            agg_landmark,
            db,
            category_filter=category,
            k=5
        )
        
        # 9. Top-K results
        bbox = face.bbox.tolist()
        results.append({
            "bbox": bbox,
            "gender": "Male" if face.gender == 1 else "Female",
            "age": int(face.age),
            "matches": [{"name": name, "confidence": float(score)} for name, score in matches]
        })

    return {
        "count": len(results),
        "results": results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
