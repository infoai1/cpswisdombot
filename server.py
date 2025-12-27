"""
CPS Wisdom Bot - FastAPI Server
FIXED: Chat alignment issue - properly identifies user vs bot messages
OPTIMIZED: Redis caching for text chat endpoint
"""

import os
import uuid
import re
import urllib.parse
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from livekit import api
from dotenv import load_dotenv
import httpx
import json
import hashlib
from typing import Optional

# Optional Redis import - server works without it (just no caching)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️ Redis not installed. Caching disabled. Install with: pip install redis")

load_dotenv()
app = FastAPI()
API_KEY = os.getenv("LIVEKIT_API_KEY")
API_SECRET = os.getenv("LIVEKIT_API_SECRET")

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
    """Generate cache key from query"""
    return f"lightrag:chat:{hashlib.md5(query.lower().strip().encode()).hexdigest()}"

BOOK_MAP = {
    "The Age of Peace": "The-Age-of-Peace.pdf",
    "The Philosophy of Peace": "The-Philosophy-of-Peace.pdf",
    "Purpose of Creation": "Purpose-of-Creation.pdf",
    "Purpose of Life": "Purpose-of-Life.pdf",
    "Creation Plan of God": "Creation-Plan-of-God.pdf",
    "Peace in the Quran": "Peace-in-the-Quran.pdf",
    "The Ideology of Peace": "The-Ideology-of-Peace.pdf",
    "Islam and Peace": "Islam-and-Peace.pdf",
}

def format_response(text):
    text = re.sub(r'###\s*(.+)', r'<h3>\1</h3>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'^-\s+(.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'\n\n', '</p><p>', text)
    for book, pdf in BOOK_MAP.items():
        encoded = urllib.parse.quote(pdf)
        link = f'<a href="/pdfs/{encoded}" target="_blank">{book} 📥</a>'
        text = re.sub(rf'\[?\d*\]?\s*{re.escape(book)}', link, text, flags=re.IGNORECASE)
    return f'<p>{text}</p>'

@app.get("/voice/")
async def get_page():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CPS Wisdom</title>
    <script src="https://cdn.jsdelivr.net/npm/livekit-client/dist/livekit-client.umd.min.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #000; color: #fff; font-family: -apple-system, system-ui, sans-serif; min-height: 100vh; display: flex; flex-direction: column; }
        #hero { position: absolute; top: 35%; left: 50%; transform: translate(-50%, -50%); text-align: center; width: 100%; transition: opacity .3s; }
        #hero h1 { font-size: 1.8rem; margin-bottom: 10px; }
        #hero p { color: #888; }
        .hide { opacity: 0; pointer-events: none; }
        
        #chat { 
            flex: 1; display: none; flex-direction: column; gap: 12px; 
            padding: 20px; padding-bottom: 100px; overflow-y: auto; 
            max-width: 700px; width: 100%; margin: 0 auto; 
        }
        #chat.show { display: flex; }

        .msg { 
            padding: 12px 16px; border-radius: 18px; 
            max-width: 75%; /* KEY: Allows movement */
            line-height: 1.5; position: relative; word-wrap: break-word; 
            animation: fadeIn .2s;
        }

        /* USER: FORCE RIGHT using Auto Margin */
        .user { 
            background: #007aff; color: white;
            margin-left: auto; /* Pushes to Right */
            margin-right: 0;
            border-bottom-right-radius: 4px; text-align: left; 
        }

        /* BOT: FORCE LEFT using Auto Margin */
        .bot { 
            background: #2c2c2e; color: white;
            margin-right: auto; /* Pushes to Left */
            margin-left: 0;
            border-bottom-left-radius: 4px; text-align: left; 
        }

        .bot p { margin: 0 0 10px 0; }
        .bot h3 { margin: 15px 0 8px 0; font-size: 1rem; color: #4a90d9; }
        .bot a { color: #4a90d9; text-decoration: underline; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .loading { background: linear-gradient(90deg, #2c2c2e, #3a3a4a, #2c2c2e); background-size: 200% 100%; animation: shimmer 1.5s infinite; }
        @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
        .dots { display: flex; gap: 4px; padding: 8px 0; }
        .dots span { width: 8px; height: 8px; border-radius: 50%; animation: rainbow 2s infinite; }
        .dots span:nth-child(1) { animation-delay: 0s; } .dots span:nth-child(2) { animation-delay: .2s; } .dots span:nth-child(3) { animation-delay: .4s; }
        @keyframes rainbow { 0%, 100% { background: #ff6b6b; transform: scale(1); } 50% { background: #ffe66d; transform: scale(1); } }
        .bar { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); width: 90%; max-width: 600px; background: #1c1c1e; border-radius: 30px; display: flex; padding: 8px 8px 8px 20px; transition: box-shadow .3s; z-index: 100; }
        input { flex: 1; background: none; border: none; color: #fff; font-size: 1rem; outline: none; }
        .btns { display: flex; gap: 8px; }
        button { width: 44px; height: 44px; border: none; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        #sendBtn { background: none; } #voiceBtn { background: #00c853; } #muteBtn { background: #444; display: none; } #endBtn { background: #ff3b30; display: none; }
        .calling #sendBtn, .calling #voiceBtn { display: none; } .calling #muteBtn, .calling #endBtn { display: flex; }
        .calling input { opacity: .3; pointer-events: none; } .calling .bar { animation: glow 2s infinite; }
        @keyframes glow { 0% { box-shadow: 0 0 15px #ff6b6b; } 50% { box-shadow: 0 0 15px #a855f7; } 100% { box-shadow: 0 0 15px #ff6b6b; } }
    </style>
</head>
<body>
    <div id="hero"><h1>Seek, Reflect, Discover</h1><p>For those who reason</p></div>
    <div id="chat"></div>
    <div class="bar">
        <input id="inp" placeholder="Ask about life, peace, Spirituality..." onkeydown="if(event.key==='Enter')sendText()">
        <div class="btns">
            <button id="sendBtn" onclick="sendText()"><svg width="24" height="24" fill="#007aff" viewBox="0 0 24 24"><path d="M2 21l21-9-21-9v7l15 2-15 2z"/></svg></button>
            <button id="voiceBtn" onclick="startVoice()"><svg width="24" height="24" stroke="#fff" fill="none" stroke-width="2" viewBox="0 0 24 24"><path d="M12 3v18M8 7v10M16 7v10M4 10v4M20 10v4"/></svg></button>
            <button id="muteBtn" onclick="toggleMute()"><svg width="20" height="20" fill="#fff" viewBox="0 0 24 24"><path d="M12 14a3 3 0 003-3V5a3 3 0 00-6 0v6a3 3 0 003 3zm5-3a5 5 0 01-10 0H5a7 7 0 006 6.92V21h2v-3.08A7 7 0 0019 11h-2z"/><line x1="4" y1="4" x2="20" y2="20" stroke="#fff" stroke-width="2"/></svg></button>
            <button id="endBtn" onclick="endVoice()"><svg width="24" height="24" fill="#fff" viewBox="0 0 24 24"><path d="M12 9c-1.6 0-3.15.25-4.6.72v3.1c0 .39.23.74.56.9.98.47 1.87 1.11 2.66 1.85.18.17.44.2.7.03L12 13.08l.68 2.52c.26.17.52.14.7-.03.79-.74 1.68-1.38 2.66-1.85.33-.16.56-.51.56-.9v-3.1C15.15 9.25 13.6 9 12 9z"/></svg></button>
        </div>
    </div>
<script>
var room = null, ub = null, bb = null, ld = null, muted = false, localIdentity = null;
function show() { document.getElementById('hero').classList.add('hide'); document.getElementById('chat').classList.add('show'); }
function addMsg(t, c, id) {
    var el = id ? document.getElementById(id) : null;
    if (el) { el.innerHTML = t; el.classList.remove('loading'); }
    else { el = document.createElement('div'); el.className = 'msg ' + c; if (id) el.id = id; el.innerHTML = t; document.getElementById('chat').appendChild(el); }
    var cDiv = document.getElementById('chat'); cDiv.scrollTop = cDiv.scrollHeight;
    return el;
}
function loading(on) { if (on && !ld) { ld = addMsg('<div class="dots"><span></span><span></span><span></span></div>', 'bot loading', 'ld'); } if (!on && ld) { ld.remove(); ld = null; } }
async function startVoice() {
    show(); document.body.classList.add('calling');
    try {
        var t = await (await fetch('/voice/token')).json();
        room = new LivekitClient.Room();
        
        // Store local identity when connected
        room.on('connected', function() {
            localIdentity = room.localParticipant?.identity || null;
            console.log('✅ Connected. Local identity:', localIdentity);
        });
        
        room.on('trackSubscribed', function(track) { if (track.kind === 'audio') { var a = track.attach(); a.volume = 1; document.body.appendChild(a); a.play(); } });
        
        // FIXED: Improved participant identification
        room.on('transcriptionReceived', function(segs) {
            segs.forEach(function(s) {
                // Extract participant identity - handle multiple formats
                var participant = s.participant;
                var pid = null;
                
                // Try different ways to get identity
                if (typeof participant === 'string') {
                    pid = participant;
                } else if (participant && participant.identity) {
                    pid = participant.identity;
                } else if (participant && participant.sid) {
                    // Check if it matches local participant
                    if (room.localParticipant && participant.sid === room.localParticipant.sid) {
                        pid = room.localParticipant.identity;
                    }
                }
                
                // Determine if this is from user (local participant) or bot (agent)
                // User identity starts with 'user_' based on token generation
                var isUser = false;
                if (pid) {
                    // Method 1: Check if starts with 'user_'
                    isUser = pid.startsWith('user_');
                    // Method 2: Check if matches local participant identity
                    if (!isUser && localIdentity) {
                        isUser = (pid === localIdentity);
                    }
                    // Method 3: Check if it's NOT an agent/bot
                    if (!isUser && (pid.includes('agent') || pid.includes('bot'))) {
                        isUser = false;
                    }
                } else {
                    // If we can't determine, default to user (safer for alignment)
                    isUser = true;
                }
                
                console.log('🔍 Transcription DEBUG:', {
                    text: s.text,
                    participant: pid,
                    localIdentity: localIdentity,
                    isUser: isUser,
                    final: s.final
                });
                
                if (isUser) {
                    // USER MESSAGE - Right aligned
                    if (!ub) ub = 'u' + Date.now();
                    addMsg(s.text, 'user', ub);
                    if (s.final) { ub = null; loading(true); }
                } else {
                    // BOT MESSAGE - Left aligned
                    loading(false);
                    if (!bb) bb = 'b' + Date.now();
                    addMsg(s.text, 'bot', bb);
                    if (s.final) bb = null;
                }
            });
        });
        
        await room.connect('wss://livekit.spiritualmessage.org', t.token);
        await room.localParticipant.setMicrophoneEnabled(true);
    } catch (e) { console.error('❌ Connection error:', e); endVoice(); }
}
function toggleMute() { if (!room) return; muted = !muted; room.localParticipant.setMicrophoneEnabled(!muted); document.getElementById('muteBtn').style.background = muted ? '#fff' : '#444'; document.getElementById('muteBtn').querySelector('svg').style.fill = muted ? '#000' : '#fff'; }
function endVoice() { if (room) room.disconnect(); room = null; ub = null; bb = null; muted = false; localIdentity = null; document.body.classList.remove('calling'); document.getElementById('muteBtn').style.background = '#444'; loading(false); }
async function sendText() {
    var i = document.getElementById('inp'), q = i.value.trim();
    if (!q) return; if (room) endVoice(); show(); i.value = ''; addMsg(q, 'user'); loading(true);
    try { var r = await fetch('/voice/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: q }) }); var d = await r.json(); loading(false); addMsg(d.answer || 'No response.', 'bot'); } catch (e) { loading(false); addMsg('Error.', 'bot'); }
}
</script>
</body>
</html>
""")

@app.post("/voice/chat")
async def chat_endpoint(data: dict):
    """Text chat endpoint with Redis caching"""
    q = data.get("question", "").strip()
    if not q:
        return {"answer": ""}
    
    # Handle greetings
    if q.lower() in ["hi", "hello", "salam", "hey"]:
        return {"answer": "Peace be upon you. How can I help?"}
    
    # Check cache first
    cache_key = get_cache_key(q)
    redis_cli = get_redis_client()
    
    if redis_cli:
        try:
            cached = redis_cli.get(cache_key)
            if cached:
                result = json.loads(cached)
                return {"answer": format_response(result.get("response", ""))}
        except Exception:
            pass
    
    # Query LightRAG
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.post("http://127.0.0.1:9621/query", json={"query": q, "mode": "mix"})
            if resp.status_code == 200:
                raw = resp.json().get("response", "No answer.")
                
                # Cache the result
                if redis_cli:
                    try:
                        redis_cli.setex(cache_key, 3600, json.dumps({"response": raw}))
                    except Exception:
                        pass
                
                return {"answer": format_response(raw)}
        except Exception:
            pass
    
    return {"answer": "Connection error."}

@app.get("/voice/token")
async def get_token():
    """Generate LiveKit access token with user_ prefix for easy identification"""
    t = api.AccessToken(API_KEY, API_SECRET).with_identity("user_" + uuid.uuid4().hex[:6]).with_grants(api.VideoGrants(room_join=True, room="voice-room"))
    return {"token": t.to_jwt()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
