# Quick Fix: Install Redis Module

## Problem
```
ModuleNotFoundError: No module named 'redis'
```

## Solution

Run this command on your server:

```bash
cd /root/my_agent
source venv/bin/activate
pip install redis
```

## Verify Installation

```bash
python -c "import redis; print('✅ Redis installed')"
```

## Restart Agent

After installing, restart the agent:

```bash
pkill -f "python.*agent"
sleep 2
python agent.py dev > agent.log 2>&1 &
```

## Check Logs

```bash
tail -f agent.log
```

You should see:
- `✅ Redis connected for caching` (if Redis is running)
- OR `⚠️ Redis connection failed: ...` (if Redis not running, but agent still works)

---

## Note

The code has been updated to work **without Redis** (caching just won't work). But for best performance, install Redis:

```bash
pip install redis
```

Then the agent will automatically use caching when Redis is available.

