#!/bin/bash
# Manual deploy script - run on your VPS

set -e

cd /root/my_agent
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --quiet
pkill -f agent.py || true
nohup python agent.py dev > agent.log 2>&1 &
sleep 2
pgrep -f agent.py && echo "Deploy SUCCESS" || echo "Deploy FAILED"
