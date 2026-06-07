import httpx
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

async def test_gonka():
    url = "https://hskyauefqcgbvgvxkluj.supabase.co/functions/v1/gonka/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "Qwen/Qwen3-235B-A22B-Instruct-2507-FP8",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, World!'"}
        ],
        "temperature": 0.7,
        "stream": False,
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

asyncio.run(test_gonka())