import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from core.face_engine import get_faces
from core.clip_engine import get_clip_embedding
from core.matcher import find_match
from core.database import load_db
import io
from PIL import Image

app = FastAPI(title="Celeb Lookalike API")

# Configure CORS for Svelte frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
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
    return {"message": "Celeb Lookalike API is running"}

@app.post("/analyze")
async def analyze_face(file: UploadFile = File(...)):
    if not db:
        return {"error": "Database not loaded. Run --build first."}

    # Read image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if frame is None:
        return {"error": "Invalid image format"}

    # Detect faces
    detections = get_faces(frame)
    
    if not detections:
        return {"results": [], "count": 0}

    results = []
    for face in detections:
        # Get CLIP embedding for multimodal matching
        clip_embedding = get_clip_embedding(frame)
        
        # Find matches
        matches = find_match(
            face.embedding, 
            clip_embedding, 
            face.gender, 
            face.age, 
            db, 
            k=5
        )
        
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
