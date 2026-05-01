import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from core.face_engine import get_faces
from core.matcher import find_match
from core.database import load_db
import io
import time
import requests
import re
import asyncio
import torch
import imagehash
import json
from PIL import Image
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from duckduckgo_search import DDGS
from datetime import datetime, timedelta
from transformers import CLIPProcessor, CLIPModel

app = FastAPI(title="Celeb Lookalike API - New Engine")

# --- Multi-frame Aggregation State ---
# Stores recent embeddings/landmarks per client IP to smooth results
aggregation_buffers = {}
BUFFER_MAX = 5
BUFFER_TIMEOUT = 10.0 # Seconds before resetting buffer

# Configure CORS for Svelte frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global database variable
db = None

# --- CLIP Model Loading ---
print("Loading CLIP model (openai/clip-vit-base-patch32)...")
device = "cuda" if torch.cuda.is_available() else "cpu"
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
print(f"CLIP loaded on {device}")

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

# --- Shared Utilities ---

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

# --- Advanced Image Search Engine ---

def fetch_candidate_images(q: str, limit: int = 30):
    """Fetch raw URLs from DDG and Bing with better fallbacks."""
    queries = [q, f"{q} portrait", f"{q} face headshot"]
    all_urls = []
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Try DDG first (parallel queries)
        ddg_results = list(executor.map(lambda q: get_ddg_images(q, 15), queries))
        for res in ddg_results: all_urls.extend(res)
        
        # If we have very few, supplement with Bing
        if len(all_urls) < 10:
            bing_results = list(executor.map(lambda q: search_bing_images(q, 15), queries))
            for res in bing_results: all_urls.extend(res)

    return list(dict.fromkeys(all_urls))[:limit]

def download_and_validate(url, timeout=3):
    """Download image and perform basic validation."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200 and "image" in response.headers.get("Content-Type", "").lower():
            img = Image.open(io.BytesIO(response.content)).convert("RGB")
            if img.width < 100 or img.height < 100: return None
            return img, url
    except:
        pass
    return None

def get_image_hash(img):
    """Compute perceptual hash for diversity filtering."""
    try:
        return imagehash.phash(img)
    except:
        return None


def filter_faces_batch(candidates, query=""):
    """Process faces sequentially and compute hashes."""
    processed = []
    seen_hashes = []
    
    for img, url in candidates:
        try:
            # 1. Diversity Check (Perceptual Hash)
            h = get_image_hash(img)
            is_duplicate = False
            if h:
                for sh in seen_hashes:
                    if h - sh < 10: # Similarity threshold
                        is_duplicate = True
                        break
            if is_duplicate: continue
            seen_hashes.append(h)

            # 2. Face Detection
            detect_img = img.copy()
            detect_img.thumbnail((640, 640))
            open_cv_image = cv2.cvtColor(np.array(detect_img), cv2.COLOR_RGB2BGR)
            faces = get_faces(open_cv_image)
            
            has_face = len(faces) > 0
            processed.append({
                "image": img,
                "url": url,
                "has_face": has_face
            })
            
            if len(processed) >= 15: break # Early stop for performance
        except Exception as e:
            print(f"Face filter error for {url}: {e}")
    return processed

def compute_clip_scores(query, candidates):
    """Rank images using CLIP semantic similarity."""
    if not candidates:
        return []
        
    clip_images = [c["image"].resize((224, 224)) for c in candidates]
    
    with torch.no_grad():
        inputs = clip_processor(
            text=[f"a portrait of {query}"], 
            images=clip_images, 
            return_tensors="pt", 
            padding=True
        ).to(device)
        
        outputs = clip_model(**inputs)
        logits_per_image = outputs.logits_per_image 
        probs = logits_per_image.softmax(dim=0).cpu().numpy()
        
    scored = []
    for i, candidate in enumerate(candidates):
        score = float(probs[i][0])
        # Boost if it has a face
        if candidate.get("has_face"):
            score *= 1.5
        
        scored.append({
            "url": candidate["url"],
            "score": score
        })
    return scored

@app.get("/search_images")
async def search_images(q: str):
    async def event_generator():
        try:
            # 1. Check Cache
            cached_res = search_cache.get(q)
            if cached_res:
                yield {"event": "phase2", "data": json.dumps(cached_res)}
                return

            # PHASE 1: Quick Results (Streaming immediately)
            candidate_urls = fetch_candidate_images(q, limit=20)
            phase1_results = []
            for i, url in enumerate(candidate_urls[:10]):
                phase1_results.append({
                    "name": f"{q.title()} (Searching...)",
                    "confidence": 0.5,
                    "image": url
                })
            yield {"event": "phase1", "data": json.dumps(phase1_results)}

            # PHASE 2: Deep Processing (Refining in background)
            download_start = time.time()
            downloaded = []
            with ThreadPoolExecutor(max_workers=10) as executor:
                results = list(executor.map(lambda u: download_and_validate(u, timeout=2), candidate_urls))
                downloaded = [r for r in results if r is not None]

            if downloaded:
                processed = filter_faces_batch(downloaded, query=q)
                scored = compute_clip_scores(q, processed)
                scored.sort(key=lambda x: x["score"], reverse=True)

                final_results = []
                for i, res in enumerate(scored[:10]):
                    count = i + 1
                    final_results.append({
                        "name": f"{q.title()} ({count})" if count > 1 else q.title(),
                        "confidence": 1.0,
                        "image": res["url"]
                    })
                
                search_cache.set(q, final_results)
                yield {"event": "phase2", "data": json.dumps(final_results)}
            else:
                # If no images could be downloaded, just repeat phase 1 as phase 2 to end refining
                yield {"event": "phase2", "data": json.dumps(phase1_results)}

        except Exception as e:
            print(f"Streaming error: {e}")
            yield {"event": "error", "data": str(e)}

    return EventSourceResponse(event_generator())

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

