"""
CPS Wisdom Bot - FastAPI Server (Refactored)
Serves static files and provides API endpoints
"""
import os
import uuid
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from livekit import api
from dotenv import load_dotenv
import httpx
import json
import hashlib
from typing import Optional

# Optional Redis import
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️ Redis not installed. Caching disabled.")

load_dotenv()
app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

API_KEY = os.getenv("LIVEKIT_API_KEY")
API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# Redis connection
redis_client = None

def get_redis_client():
    """Get or create Redis client"""
    global redis_client
    if not REDIS_AVAILABLE:
        return None
    if redis_client is None:
        try:
            redis_client = redis.Redis(
                host='127.0.0.1',
                port=6380,
                db=0,
                decode_responses=True,
                socket_connect_timeout=2
            )
            redis_client.ping()
        except Exception:
            redis_client = None
    return redis_client

def get_cache_key(query: str) -> str:
    """Generate cache key"""
    return f"lightrag:chat:{hashlib.md5(query.lower().strip().encode()).hexdigest()}"

@app.get("/voice/")
async def get_page():
    """Serve the main HTML page"""
    return FileResponse("templates/index.html")

@app.post("/voice/chat")
async def chat_endpoint(data: dict):
    """Text chat endpoint with Redis caching"""
    q = data.get("question", "").strip()
    if not q:
        return {"answer": ""}

    # Handle greetings
    if q.lower() in ["hi", "hello", "salam", "hey"]:
        return {"answer": "Peace be upon you. How can I help?"}

    # Check cache
    cache_key = get_cache_key(q)
    redis_cli = get_redis_client()

    if redis_cli:
        try:
            cached = redis_cli.get(cache_key)
            if cached:
                result = json.loads(cached)
                return {"answer": result.get("response", "")}
        except Exception:
            pass

    # Query LightRAG
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.post("http://127.0.0.1:9621/query", json={"query": q, "mode": "naive"})
            if resp.status_code == 200:
                raw = resp.json().get("response", "No answer.")

                # Cache the result
                if redis_cli:
                    try:
                        redis_cli.setex(cache_key, 3600, json.dumps({"response": raw}))
                    except Exception:
                        pass

                return {"answer": raw}
        except Exception:
            pass

    return {"answer": "Connection error."}

@app.get("/voice/token")
async def get_token():
    """Generate LiveKit access token"""
    t = api.AccessToken(API_KEY, API_SECRET).with_identity("user_" + uuid.uuid4().hex[:6]).with_grants(api.VideoGrants(room_join=True, room="voice-room"))
    return {"token": t.to_jwt()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
