import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


class LlmService:
    @staticmethod
    def generate_stream(prompt: str):
        llm_response = model.generate_content(prompt)
        return llm_response.text
