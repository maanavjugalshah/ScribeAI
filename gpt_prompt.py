import os
import requests
import json
from dotenv import load_dotenv

# Load .env variables if available
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_gemini_response(prompt_text):
    if not GEMINI_API_KEY:
        raise ValueError("Missing GEMINI_API_KEY environment variable.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    body = {
        "contents": [
            {
                "parts": [{"text": prompt_text}]
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("❌ Error calling Gemini API:", e)
        return None

# Optional test
if __name__ == "__main__":
    test_prompt = "Write a haiku about the moon."
    print(get_gemini_response(test_prompt))
