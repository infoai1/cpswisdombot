# Deployment Guide - Optimized CPS Wisdom Bot

## 🚀 Quick Deployment

### Step 1: Backup Current Files
```bash
cd /root/my_agent
cp agent.py agent.py.backup
cp server.py server.py.backup
```

### Step 2: Upload New Files
Upload the optimized files to `/root/my_agent/`:
- `agent.py` (with caching, streaming, optimized VAD)
- `server.py` (with fixed chat alignment)

### Step 3: Install Dependencies (if needed)
```bash
cd /root/my_agent
source venv/bin/activate
pip install redis aiohttp  # If not already installed
```

### Step 4: Restart Services
```bash
cd /root/my_agent
source venv/bin/activate

# Stop existing processes
pkill -f "python.*agent"
pkill -f "python.*server"
sleep 2

# Start optimized services
python server.py > server.log 2>&1 &
python agent.py dev > agent.log 2>&1 &

# Verify they're running
ps aux | grep -E "agent|server" | grep -v grep
```

### Step 5: Test
1. Open browser to `https://livekit.spiritualmessage.org`
2. Click "Connect"
3. Speak a message - verify it appears on the RIGHT
4. Ask a question - verify bot responds on the LEFT
5. Ask the same question again - should be faster (cached)

---

## ✅ Verification Checklist

- [ ] Redis is running on port 6380
- [ ] Services started without errors
- [ ] Chat alignment: User messages on RIGHT
- [ ] Chat alignment: Bot messages on LEFT
- [ ] Cache working (check logs for "Cache HIT")
- [ ] Response time improved

---

## 🔍 Troubleshooting

### If agent.py fails to start:
1. Check logs: `tail -50 /root/my_agent/agent.log`
2. Verify API keys in `.env`
3. Check LiveKit connection: `curl http://127.0.0.1:7880`

### If alignment still wrong:
1. Open browser console (F12)
2. Check transcription logs
3. Verify `room.localParticipant.identity` is set
4. Check server logs: `tail -50 /root/my_agent/server.log`

### If cache not working:
1. Test Redis: `redis-cli -p 6380 ping`
2. Check agent logs for cache errors
3. Verify Redis connection in code

---

## 📊 Expected Results

**Before Optimization:**
- Response time: 1-4 seconds
- Repeated queries: 0.4s each
- User messages: Sometimes misaligned

**After Optimization:**
- Response time: 1-4 seconds (first time)
- Repeated queries: <10ms (cached)
- User messages: Always right-aligned
- Perceived latency: 50-70% faster (streaming)

---

*Deploy with confidence! 🎉*

