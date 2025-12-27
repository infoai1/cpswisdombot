"""
LLM Quality Comparison: Gemini vs Groq Llama
============================================
This script compares response quality between Google Gemini and Groq Llama
using YOUR LightRAG knowledge base.

SETUP:
1. Get free Groq API key: https://console.groq.com
2. Run: export GROQ_API_KEY="your-key-here"
3. Run: python compare_llms.py

The script will show side-by-side responses so you can judge quality.
"""

import asyncio
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Check for API keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GROQ_API_KEY:
    print("\n❌ GROQ_API_KEY not found!")
    print("   Get free key: https://console.groq.com")
    print("   Then run: export GROQ_API_KEY='your-key-here'\n")
    exit(1)

if not GOOGLE_API_KEY:
    print("\n⚠️  GOOGLE_API_KEY not found - will skip Gemini comparison")
    print("   Set it with: export GOOGLE_API_KEY='your-key-here'\n")

import httpx

# Test questions about Islamic wisdom
TEST_QUESTIONS = [
    "What is the concept of peace in Islam?",
    "How should a Muslim respond to criticism?",
    "What is the purpose of life according to Islamic teachings?",
    "How does Islam view patience and gratitude?",
    "What is true jihad according to Maulana Wahiduddin Khan?",
]

SYSTEM_PROMPT = """You are CPS Wisdom Bot. Answer based ONLY on the provided context.
Rules:
- Answer in 1-2 sentences maximum
- Be direct and brief
- Say "Maulana Wahiduddin Khan teaches..." naturally
- If context doesn't help, say "This isn't in my library."
"""

async def query_lightrag(question: str) -> str:
    """Get context from LightRAG"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "http://127.0.0.1:9621/query",
                json={"query": question, "mode": "naive"}
            )
            if resp.status_code == 200:
                return resp.json().get("response", "")
    except Exception as e:
        print(f"⚠️ LightRAG error: {e}")
    return ""

async def query_groq(question: str, context: str) -> tuple[str, float]:
    """Query Groq Llama 3.1 70B"""
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-70b-versatile",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
                    ],
                    "max_tokens": 150,
                    "temperature": 0.3
                }
            )
            elapsed = (time.time() - start) * 1000
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"], elapsed
            else:
                return f"Error: {resp.status_code} - {resp.text}", elapsed
    except Exception as e:
        return f"Error: {e}", (time.time() - start) * 1000

async def query_gemini(question: str, context: str) -> tuple[str, float]:
    """Query Google Gemini"""
    if not GOOGLE_API_KEY:
        return "SKIPPED (no API key)", 0

    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{
                        "parts": [{
                            "text": f"{SYSTEM_PROMPT}\n\nContext:\n{context}\n\nQuestion: {question}"
                        }]
                    }],
                    "generationConfig": {
                        "maxOutputTokens": 150,
                        "temperature": 0.3
                    }
                }
            )
            elapsed = (time.time() - start) * 1000
            if resp.status_code == 200:
                data = resp.json()
                text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No response")
                return text, elapsed
            else:
                return f"Error: {resp.status_code}", elapsed
    except Exception as e:
        return f"Error: {e}", (time.time() - start) * 1000

def print_comparison(question: str, gemini_resp: str, gemini_time: float, groq_resp: str, groq_time: float):
    """Print side-by-side comparison"""
    print("\n" + "="*80)
    print(f"📝 QUESTION: {question}")
    print("="*80)

    print(f"\n🔵 GEMINI ({gemini_time:.0f}ms):")
    print("-" * 40)
    print(gemini_resp[:500])

    print(f"\n🟢 GROQ LLAMA 3.1 70B ({groq_time:.0f}ms):")
    print("-" * 40)
    print(groq_resp[:500])

    print(f"\n⏱️  Speed difference: Groq is {gemini_time/max(groq_time,1):.1f}x faster")

async def main():
    print("\n" + "🔬 "*20)
    print("   LLM QUALITY COMPARISON: GEMINI vs GROQ LLAMA")
    print("🔬 "*20)
    print("\nThis test uses YOUR LightRAG knowledge base.")
    print("Compare the responses and decide which is better for your use case.\n")

    total_gemini_time = 0
    total_groq_time = 0

    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n[{i}/{len(TEST_QUESTIONS)}] Fetching context from LightRAG...")
        context = await query_lightrag(question)

        if not context:
            print(f"⚠️ No context found for: {question}")
            continue

        # Query both LLMs in parallel
        gemini_task = query_gemini(question, context[:2000])
        groq_task = query_groq(question, context[:2000])

        (gemini_resp, gemini_time), (groq_resp, groq_time) = await asyncio.gather(gemini_task, groq_task)

        total_gemini_time += gemini_time
        total_groq_time += groq_time

        print_comparison(question, gemini_resp, gemini_time, groq_resp, groq_time)

        # Small delay to avoid rate limits
        await asyncio.sleep(0.5)

    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"Total Gemini time:  {total_gemini_time:.0f}ms ({total_gemini_time/1000:.1f}s)")
    print(f"Total Groq time:    {total_groq_time:.0f}ms ({total_groq_time/1000:.1f}s)")
    print(f"Speed improvement:  {total_gemini_time/max(total_groq_time,1):.1f}x faster with Groq")
    print("\n💡 Review the responses above. If Groq quality is acceptable,")
    print("   switching will reduce your voice response time significantly!")
    print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(main())
