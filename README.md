# CPS Wisdom Bot - Voice Agent Technical Handover

**Project:** CPS Wisdom Bot Voice Integration  
**Domain:** livekit.spiritualmessage.org  
**Server:** Hetzner 32GB Ubuntu (docker-ce-ubuntu-32gb-hel1-1)  
**Date:** December 26, 2025

---

## 1. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER BROWSER (WebRTC)                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     NGINX (Port 443) - SSL Termination                       │
│                     livekit.spiritualmessage.org                             │
└─────────────────────────────────────────────────────────────────────────────┘
                          │                           │
                          ▼                           ▼
┌──────────────────────────────────┐    ┌──────────────────────────────────────┐
│   Flask Frontend (Port 8000)     │    │   LiveKit Server (Port 7880)         │
│   /root/my_agent/server.py       │    │   WebRTC Media Server                │
│   - Serves voice UI              │    │   - Handles audio streams            │
│   - Token generation             │    │   - Room management                  │
│   - Text chat endpoint           │    │   - UDP: 50000-60000                 │
└──────────────────────────────────┘    └──────────────────────────────────────┘
                                                      │
                                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        VOICE AGENT (agent.py)                                │
│   Pipeline: STT (OpenAI) → LLM (Gemini 3 Flash) → TTS (OpenAI Nova)         │
│   VAD: Silero (min_silence: 0.8s)                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     LightRAG (Port 9621) - Knowledge Base                    │
│   Mode: naive (vector search only)                                          │
│   Content: Maulana Wahiduddin Khan's 145 books (~50M tokens)                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. FILE LOCATIONS

| File | Path | Purpose |
|------|------|---------|
| Voice Agent | `/root/my_agent/agent.py` | Main agent logic, tool definitions |
| Environment | `/root/my_agent/.env` | API keys (LIVEKIT, OPENAI, GOOGLE) |
| Frontend Server | `/root/my_agent/server.py` | Flask app serving voice UI |
| LiveKit Config | `/root/livekit/livekit.spiritualmessage.org/livekit.yaml` | LiveKit server settings |
| Agent Logs | `/root/my_agent/agent.log` | Runtime logs |
| Server Logs | `/root/my_agent/server.log` | Frontend logs |
| Python venv | `/root/my_agent/venv/` | Virtual environment |

---

## 3. RUNNING SERVICES

| Service | Container/Process | Port | Status |
|---------|-------------------|------|--------|
| LiveKit Server | `livekitspiritualmessageorg-livekit-1` | 7880 (HTTP), 7881 (TCP), 50000-60000 (UDP) | Docker |
| LiveKit Redis | `livekitspiritualmessageorg-redis-1` | 6380 | Docker |
| LightRAG | `lightrag` | 9621 | Docker |
| RAGflow | `docker-ragflow-cpu-1` | 9380-9382, 8080 | Docker |
| RAGflow Redis | `docker-redis-1` | 6379 | Docker |
| Elasticsearch | `docker-es01-1` | 1200 | Docker |
| Voice Agent | Python process | - | Manual start |
| Frontend | Python process | 8000 | Manual start |

---

## 4. CURRENT CONFIGURATION

### agent.py (Current)
```python
# STT: OpenAI Whisper
# LLM: Google Gemini 3 Flash Preview
# TTS: OpenAI Nova voice
# VAD: Silero (0.8s silence threshold)
# RAG: LightRAG naive mode (vector search only)

session = AgentSession(
    vad=silero.VAD.load(min_silence_duration=0.8),
    stt=openai.STT(),
    llm=google.LLM(model="gemini-3-flash-preview"),
    tts=openai.TTS(voice="nova"),
)
```

### .env Required Keys
```
LIVEKIT_URL=ws://127.0.0.1:7880
LIVEKIT_API_KEY=<from livekit.yaml>
LIVEKIT_API_SECRET=<from livekit.yaml>
OPENAI_API_KEY=<openai key>
GOOGLE_API_KEY=<google ai studio key>
```

---

## 5. START/STOP COMMANDS

### Start Services
```bash
# Activate venv
cd /root/my_agent && source venv/bin/activate

# Start Voice Agent
pkill -f "python.*agent"; sleep 1
python agent.py dev > agent.log 2>&1 &

# Start Frontend Server  
pkill -f "python.*server"; sleep 1
python server.py > server.log 2>&1 &

# Check status
ps aux | grep -E "agent|server" | grep -v grep
```

### View Logs
```bash
# Agent logs
tail -50 /root/my_agent/agent.log

# Server logs
tail -50 /root/my_agent/server.log
```

### Restart LiveKit (if needed)
```bash
cd /root/livekit/livekit.spiritualmessage.org
docker compose restart
```

---

## 6. ISSUES RESOLVED (Dec 25-26, 2025)

### Issue 1: Chat Bubble Alignment
- **Problem:** User messages aligned left instead of right
- **Root Cause:** Voice transcription participant identity returned as string, not object
- **Fix:** Updated JS to handle both formats
- **File:** `/root/my_agent/server.py` (line ~134)

### Issue 2: Server 502 Errors
- **Problem:** server.py file corrupted during upload
- **Fix:** Re-uploaded complete file

### Issue 3: WebRTC ICE Failures
- **Problem:** Browser couldn't establish connection
- **Root Cause:** UFW blocking UDP ports
- **Fix:** 
```bash
ufw allow 7882/udp
ufw allow 50000:60000/udp
```

### Issue 4: LiveKit "Keys must be provided" Error
- **Problem:** livekit.yaml regenerated without credentials
- **Fix:** Restored API keys in `/root/livekit/livekit.spiritualmessage.org/livekit.yaml`

### Issue 5: Redis NOAUTH Error
- **Problem:** LiveKit connecting to wrong Redis (RAGflow's on 6379 with auth)
- **Fix:** Changed livekit.yaml to use `127.0.0.1:6380` (LiveKit's dedicated Redis)

### Issue 6: Agent WebSocket 502
- **Problem:** Agent using public URL through nginx
- **Fix:** Changed LIVEKIT_URL from `wss://livekit.spiritualmessage.org` to `ws://127.0.0.1:7880` in .env

---

## 7. LATENCY ANALYSIS

### Pipeline Breakdown
| Component | Measured Latency |
|-----------|------------------|
| OpenAI STT | ~100-200ms |
| Gemini 3 Flash LLM | ~500-2000ms |
| LightRAG naive | **0.4s** |
| LightRAG mix | **1.3s** |
| OpenAI TTS | ~200-500ms |
| **Total Expected** | **1-4 seconds** |

### Benchmark Results
```bash
# LightRAG naive mode
curl -X POST http://127.0.0.1:9621/query -d '{"query":"what is peace","mode":"naive"}'
# Result: 0.432s

# LightRAG mix mode  
curl -X POST http://127.0.0.1:9621/query -d '{"query":"what is peace","mode":"mix"}'
# Result: 1.267s
```

### Current Decision
Using **naive mode** for faster response (~0.4s vs 1.3s). Mix mode adds graph traversal which increases latency without significant quality improvement for most queries.

---

## 8. KNOWN LIMITATIONS

1. **User Interruptions:** If user speaks while agent is searching, speech gets cancelled. Log shows: `speech not done in time after interruption`

2. **No Caching:** Repeated queries hit LightRAG every time. Redis caching could improve this.

3. **Voice-only Feedback:** No visual "thinking" indicator during search. Consider adding UI feedback.

4. **Single Room:** All users join same "voice-room". For multi-user, need dynamic room creation.

---

## 9. FUTURE IMPROVEMENTS

### High Priority
- [ ] Add Redis caching for frequent queries
- [ ] Implement "Let me check..." voice feedback before tool calls
- [ ] Add visual loading state in UI during search

### Medium Priority
- [ ] Switch to Gemini's native STT/TTS (requires Google Cloud credentials, not just API key)
- [ ] Add response streaming for faster perceived latency
- [ ] Implement conversation history/context

### Low Priority
- [ ] Multi-room support
- [ ] Analytics/usage tracking
- [ ] Rate limiting per user

---

## 10. TROUBLESHOOTING

### Agent Not Responding
```bash
# Check if running
ps aux | grep agent

# Check logs
tail -50 /root/my_agent/agent.log

# Restart
pkill -f "python.*agent"
cd /root/my_agent && source venv/bin/activate
python agent.py dev > agent.log 2>&1 &
```

### Voice Not Working in Browser
1. Check browser console for errors (F12)
2. Verify microphone permissions granted
3. Check LiveKit container: `docker logs livekitspiritualmessageorg-livekit-1`

### LightRAG Slow/Down
```bash
# Test directly
curl -X POST http://127.0.0.1:9621/query -H "Content-Type: application/json" -d '{"query":"test","mode":"naive"}'

# Check container
docker logs lightrag --tail 50
docker restart lightrag
```

### Redis Connection Issues
```bash
# LiveKit Redis (no auth)
redis-cli -p 6380 ping

# RAGflow Redis (has auth)
redis-cli -p 6379 ping
```

---

## 11. CONTACTS & RESOURCES

- **LiveKit Docs:** https://docs.livekit.io/agents/
- **LightRAG API:** http://127.0.0.1:9621 (local only)
- **Gemini API:** https://aistudio.google.com/
- **Domain:** livekit.spiritualmessage.org

---

## 12. QUICK REFERENCE

```bash
# Full restart sequence
cd /root/my_agent && source venv/bin/activate
pkill -f "python.*agent"; pkill -f "python.*server"
sleep 2
python server.py > server.log 2>&1 &
python agent.py dev > agent.log 2>&1 &
echo "Services started. Check: ps aux | grep python"
```

---

*Document generated: December 26, 2025* so give me solution how can make my bot faster and while i use my voice agent it recognises user input as bot input hence thealignment is left not right
