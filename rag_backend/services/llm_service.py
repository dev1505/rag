import os
from dotenv import load_dotenv
import google.generativeai as genai
import json

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


class LlmService:
    @staticmethod
    def generate_stream(prompt: str):
        stream = model.generate_content(prompt, stream=True)
        for chunk in stream:
            if chunk and hasattr(chunk, "text") and chunk.text:
                yield json.dumps({"text": chunk.text}) + "\n"
