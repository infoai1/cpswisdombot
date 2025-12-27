"""
CPS Wisdom Bot - Optimized Voice Agent
- Redis caching for faster repeated queries
- Optimized VAD (0.5s instead of 0.8s)
- Pre-call feedback for better UX
"""

import asyncio
import hashlib
import json
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, function_tool, RunContext
from livekit.agents.voice import AgentSession
from livekit.plugins import openai, silero, google
import httpx
from typing import Optional

# Optional Redis import - agent works without it (just no caching)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️ Redis not installed. Caching disabled. Install with: pip install redis")

load_dotenv()

# Redis connection for caching
redis_client = None

def get_redis_client():
    """Get or create Redis client for caching"""
    global redis_client
    if not REDIS_AVAILABLE:
        return None
    
    if redis_client is None:
        try:
            redis_client = redis.Redis(
                host='127.0.0.1',
                port=6380,  # LiveKit's Redis
                db=0,
                decode_responses=True,
                socket_connect_timeout=2
            )
            redis_client.ping()
            print("✅ Redis connected for caching")
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}. Caching disabled.")
            redis_client = None
    return redis_client

def get_cache_key(query: str) -> str:
    """Generate cache key from query"""
    return f"lightrag:query:{hashlib.md5(query.lower().strip().encode()).hexdigest()}"

async def query_lightrag_cached(query: str, mode: str = "naive") -> dict:
    """
    Query LightRAG with Redis caching
    Returns cached result if available, otherwise queries LightRAG
    """
    cache_key = get_cache_key(query)
    redis_cli = get_redis_client()
    
    # Try to get from cache
    if redis_cli:
        try:
            cached = redis_cli.get(cache_key)
            if cached:
                print(f"✅ Cache HIT: {query[:50]}...")
                return json.loads(cached)
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")
    
    # Query LightRAG
    print(f"🔍 Cache MISS - querying LightRAG: {query[:50]}...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "http://127.0.0.1:9621/query",
                json={"query": query, "mode": mode}
            )
            if resp.status_code == 200:
                result = resp.json()
                
                # Cache the result (TTL: 1 hour)
                if redis_cli:
                    try:
                        redis_cli.setex(
                            cache_key,
                            3600,  # 1 hour TTL
                            json.dumps(result)
                        )
                        print(f"💾 Cached result for: {query[:50]}...")
                    except Exception as e:
                        print(f"⚠️ Cache write error: {e}")
                
                return result
            else:
                return {"response": "Error querying knowledge base."}
    except Exception as e:
        print(f"❌ LightRAG query error: {e}")
        return {"response": "Search unavailable."}

@function_tool
async def search_knowledge(context: RunContext, question: str):
    """
    Search Islamic wisdom from Maulana Wahiduddin Khan's books.
    Use this tool to find information about peace, spirituality, and Islamic teachings.
    """
    # Query with caching
    result = await query_lightrag_cached(question, mode="naive")
    
    # Extract and format response
    response_text = result.get("response", "")
    if response_text:
        # Clean up response - remove markdown headers, bullets, short lines
        lines = [
            l.strip() 
            for l in response_text.split('\n') 
            if l.strip() 
            and not l.startswith('#') 
            and not l.startswith('-') 
            and len(l.strip()) > 20
        ]
        # Return first 4 meaningful lines, max 600 chars
        formatted = ' '.join(lines[:4])[:600]
        return formatted if formatted else "Not found."
    return "Not found."

async def entrypoint(ctx: JobContext):
    await ctx.connect()
    
    agent = Agent(
        instructions="""CPS Wisdom Bot. Source: Maulana Wahiduddin Khan's books.

RULES:
1. Questions → use search_knowledge tool, then answer in 2-3 sentences
2. Say "Maulana Wahiduddin Khan teaches..." naturally
3. Unknown topic → "This isn't covered in my library."
4. Unclear/bizarre input → "I didn't understand that. Could you please repeat your question?"
5. Keep responses short and direct
""",
        tools=[search_knowledge],
    )
    
    # OPTIMIZED: Faster VAD (0.5s instead of 0.8s) for quicker response
    session = AgentSession(
        vad=silero.VAD.load(min_silence_duration=0.5),  # Reduced from 0.8s (37.5% faster)
        stt=openai.STT(),
        llm=google.LLM(model="gemini-3-flash-preview"),
        tts=openai.TTS(voice="nova"),
    )
    
    # Start the session
    await session.start(agent=agent, room=ctx.room)

    # Auto-greet when user joins
    await session.say("Peace be upon you. How can I help?")

    # Wait indefinitely
    await asyncio.Event().wait()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
