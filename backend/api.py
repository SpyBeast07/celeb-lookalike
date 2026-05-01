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
            # Safety check for inhomogeneous shapes
            valid_lms = [l for l in buf['landmark'] if l is not None and len(l) == 4]
            if valid_lms:
                agg_landmark = np.mean(valid_lms, axis=0).tolist()

        # 8. Hybrid similarity scoring (Separate for Actors and Cartoons)
        actor_matches = find_match(
            agg_embedding, 
            face.gender, 
            face.age, 
            agg_landmark,
            db,
            category_filter="actors",
            k=5
        )
        
        cartoon_matches = find_match(
            agg_embedding, 
            face.gender, 
            face.age, 
            agg_landmark,
            db,
            category_filter="cartoons",
            k=5
        )
        
        # 9. Top-K results
        bbox = face.bbox.tolist()
        results.append({
            "bbox": bbox,
            "gender": "Male" if face.gender == 1 else "Female",
            "age": int(face.age),
            "actor_matches": [{"name": name, "confidence": float(score)} for name, score in actor_matches],
            "cartoon_matches": [{"name": name, "confidence": float(score)} for name, score in cartoon_matches]
        })

    return {
        "count": len(results),
        "results": results
    }

from duckduckgo_search import DDGS
import requests
import re
from concurrent.futures import ThreadPoolExecutor

def search_bing_images(query, limit=10):
    """Fallback scraper for Bing Images if DDG fails."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        url = f"https://www.bing.com/images/search?q={requests.utils.quote(query)}&form=HDRSC2&first=1"
        response = requests.get(url, headers=headers, timeout=10)
        # Extract image URLs from the 'm' (metadata) attribute in the HTML
        pattern = r'murl&quot;:&quot;(.*?)&quot;'
        urls = re.findall(pattern, response.text)
        return urls[:limit]
    except Exception as e:
        print(f"Bing fallback error: {e}")
        return []

@app.get("/search_images")
async def search_images(q: str):
    results = []
    seen_urls = set()
    
    # Enhanced queries as requested
    search_queries = [
        f"{q} face portrait",
        f"{q} character portrait",
        f"{q} official art",
        f"{q} close up"
    ]
    
    def get_ddg_images(query):
        try:
            with DDGS() as ddgs:
                return [res.get("image") for res in ddgs.images(query, max_results=15) if res.get("image")]
        except Exception as e:
            print(f"DDG error for {query}: {e}")
            return []

    # Try DDG first
    with ThreadPoolExecutor(max_workers=4) as executor:
        all_urls_nested = list(executor.map(get_ddg_images, search_queries))
    
    all_urls = [url for sublist in all_urls_nested for url in sublist]
    
    # Fallback to Bing if DDG is empty (likely 403)
    if not all_urls:
        print("DDG failed/blocked, falling back to Bing...")
        with ThreadPoolExecutor(max_workers=4) as executor:
            all_urls_nested = list(executor.map(lambda q: search_bing_images(q, 15), search_queries))
        all_urls = [url for sublist in all_urls_nested for url in sublist]

    for url in all_urls:
        if url not in seen_urls and len(results) < 10:
            seen_urls.add(url)
            results.append({
                "name": q.title(),
                "confidence": 1.0,
                "image": url
            })

    # Ensure exactly 10 results
    if len(results) > 0:
        while len(results) < 10:
            results.append(results[len(results) % len(results)])
    else:
        # Absolute last resort: provide placeholders if everything failed (should not happen with Bing scraper)
        for i in range(10):
            results.append({
                "name": q.title(),
                "confidence": 1.0,
                "image": "https://via.placeholder.com/600?text=No+Image+Found"
            })
            
    return {"results": results}

@app.get("/fetch_image")
async def fetch_image(q: str, type: str = "actor"):
    query = f"{q} face portrait" if type == "actor" else f"{q} cartoon character portrait"
    
    # Try DDG
    try:
        with DDGS() as ddgs:
            res = next(ddgs.images(query, max_results=1), None)
            if res and res.get("image"):
                return {"image": res["image"]}
    except:
        pass
        
    # Fallback Bing
    urls = search_bing_images(query, 1)
    if urls:
        return {"image": urls[0]}
        
    return {"image": None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

