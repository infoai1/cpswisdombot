# Verify Agent Setup

## ✅ Current Status

Your agent logs show:
- ✅ Redis installed successfully
- ✅ Agent starting up
- ✅ Connected to LiveKit (ws://127.0.0.1:7880)
- ✅ Worker registered (ID: AW_Qg6JB6VkHZNu)

## 🔍 Check Redis Connection

Run this to verify Redis is working:

```bash
# Test Redis connection
redis-cli -p 6380 ping
# Should return: PONG

# Check if agent connected to Redis
tail -20 agent.log | grep -i redis
# Should show: "✅ Redis connected for caching" (if Redis is running)
```

## 🔍 Check Full Agent Status

```bash
# Check if agent process is running
ps aux | grep "agent.py" | grep -v grep

# Check recent logs
tail -30 agent.log

# Check for any errors
tail -50 agent.log | grep -i error
```

## 🧪 Test the Agent

1. **Check server is running:**
   ```bash
   ps aux | grep "server.py" | grep -v grep
   ```

2. **If server not running, start it:**
   ```bash
   cd /root/my_agent
   source venv/bin/activate
   python server.py > server.log 2>&1 &
   ```

3. **Test in browser:**
   - Open: `https://livekit.spiritualmessage.org/voice/`
   - Click voice button
   - Speak something
   - Check alignment (your messages should be on RIGHT)

## 📊 Expected Log Messages

**Good signs:**
- `✅ Redis connected for caching` - Redis working
- `registered worker` - Agent connected to LiveKit
- `HTTP server listening` - Agent ready

**Warnings (OK):**
- `⚠️ Redis connection failed` - Agent works without Redis, just no caching
- `⚠️ Redis not installed` - Install Redis for caching

**Errors (needs fixing):**
- `ModuleNotFoundError` - Missing dependency
- `Connection refused` - Service not running
- `Authentication failed` - Wrong API keys

## 🚀 Next Steps

1. ✅ Agent is running
2. ✅ Redis installed
3. ⏭️ Test voice interaction
4. ⏭️ Verify chat alignment
5. ⏭️ Test caching (ask same question twice)

---

*Your agent should be fully operational now! 🎉*

