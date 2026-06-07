# pip install openai 'https://hskyauefqcgbvgvxkluj.supabase.co/functions/v1/gonka'
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GONKA_API_KEY"),
    base_url="https://hskyauefqcgbvgvxkluj.supabase.co/functions/v1/gonka",
)

resp = client.chat.completions.create(
    model="Qwen/Qwen3-235B-A22B-Instruct-2507-FP8",
    messages=[{"role": "user", "content": "Hello! What is GonkaAI?"}],
)
print(resp.choices[0].message.content)