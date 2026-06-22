# pip install openai 'https://hskyauefqcgbvgvxkluj.supabase.co/functions/v1/gonka'
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GONKA_API_KEY"),
    base_url="https://api.gonka-api.org/v1",
)

resp = client.chat.completions.create(
    model="MiniMaxAI/MiniMax-M2.7",
    messages=[{"role": "user", "content": "Привет! Что такое GonkaAI?"}],
)
print(resp.choices[0].message.content)

