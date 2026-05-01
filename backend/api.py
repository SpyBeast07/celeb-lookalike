import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from core.face_engine import get_faces
from core.matcher import find_match
from core.database import load_db
import io
import time
import requests
import re
import asyncio
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from duckduckgo_search import DDGS
from datetime import datetime, timedelta

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

# --- Image Search Engine Core ---

class SearchCache:
    def __init__(self, ttl_seconds=600):
        self.cache = {}
        self.ttl = ttl_seconds

    def get(self, key):
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() < entry['expiry']:
                return entry['data']
            else:
                del self.cache[key]
        return None

    def set(self, key, data):
        self.cache[key] = {
            'data': data,
            'expiry': datetime.now() + timedelta(seconds=self.ttl)
        }

search_cache = SearchCache()

def validate_image_url(url, timeout=1.5):
    """Check if URL is a valid image with a HEAD request."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}
        response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "").lower()
            return "image" in content_type
    except:
        pass
    return False

def rank_image_result(url, query):
    """
    Ranks an image result based on URL keywords and relevance to query.
    Higher score is better.
    """
    score = 0
    url_lower = url.lower()
    
    # Positive keywords (Face-focused)
    face_keywords = ["face", "portrait", "close-up", "headshot", "official", "character"]
    for kw in face_keywords:
        if kw in url_lower:
            score += 20
            
    # Resolution/Quality hints in URL
    if "high" in url_lower or "hd" in url_lower or "large" in url_lower:
        score += 10
        
    # Penalize negative keywords
    negative_keywords = ["poster", "wallpaper", "group", "full-body", "background", "landscape", "wide"]
    for kw in negative_keywords:
        if kw in url_lower:
            score -= 30
            
    # Aspect ratio hints (prefer square-ish for face cards)
    # We can't know for sure without downloading, but some URLs have hints
    if "square" in url_lower:
        score += 15

    return score

def search_bing_images(query, limit=15):
    """Robust scraper for Bing Images."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        url = f"https://www.bing.com/images/search?q={requests.utils.quote(query)}&form=HDRSC2&first=1"
        response = requests.get(url, headers=headers, timeout=5)
        pattern = r'murl&quot;:&quot;(.*?)&quot;'
        urls = re.findall(pattern, response.text)
        return urls[:limit]
    except Exception as e:
        print(f"Bing fallback error: {e}")
        return []

def get_ddg_images(query, limit=15):
    """Fetch images from DDG."""
    try:
        with DDGS() as ddgs:
            return [res.get("image") for res in ddgs.images(query, max_results=limit) if res.get("image")]
    except Exception as e:
        print(f"DDG error for {query}: {e}")
        return []

@app.get("/search_images")
async def search_images(q: str):
    # 1. Check Cache
    cached_res = search_cache.get(q)
    if cached_res:
        return {"results": cached_res}

    # 2. Enhance Queries
    enhanced_queries = [
        f"{q} face close up portrait",
        f"{q} official character headshot",
        f"{q} front face portrait"
    ]
    
    # 3. Fetch in Parallel
    all_urls = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Try DDG first
        futures = [executor.submit(get_ddg_images, query) for query in enhanced_queries]
        for f in futures:
            all_urls.extend(f.result())
            
        # Fallback to Bing if DDG was sparse
        if len(all_urls) < 10:
            futures = [executor.submit(search_bing_images, query) for query in enhanced_queries]
            for f in futures:
                all_urls.extend(f.result())

    # 4. Filter Duplicates & Rank
    unique_urls = list(dict.fromkeys(all_urls)) # Maintain order
    scored_results = []
    for url in unique_urls:
        score = rank_image_result(url, q)
        scored_results.append({"url": url, "score": score})
    
    # Sort by score descending
    scored_results.sort(key=lambda x: x["score"], reverse=True)

    # 5. Validate until we have 10
    final_results = []
    seen_urls = set()
    
    # Process in small batches for validation speed
    batch_size = 5
    with ThreadPoolExecutor(max_workers=10) as validator:
        idx = 0
        while len(final_results) < 10 and idx < len(scored_results):
            batch = scored_results[idx : idx + batch_size]
            idx += batch_size
            
            # Validate batch
            valid_map = list(validator.map(lambda x: validate_image_url(x["url"]), batch))
            
            for i, is_valid in enumerate(valid_map):
                if is_valid and len(final_results) < 10:
                    url = batch[i]["url"]
                    if url not in seen_urls:
                        seen_urls.add(url)
                        count = len(final_results) + 1
                        final_results.append({
                            "name": f"{q.title()} ({count})" if count > 1 else q.title(),
                            "confidence": 1.0,
                            "image": url
                        })

    # 6. Cache and Return
    search_cache.set(q, final_results)
    return {"results": final_results}

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

