import os
from dotenv import load_dotenv
import google.generativeai as genai
from Schema.all_schema import *

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

class Llm_Service:
    @staticmethod
    def generate_blog():
        prompt = f""
        response_from_ai = model.generate_content(prompt)
        # user_cost = (
        #     response_from_ai.usage_metadata.prompt_token_count * 0.3 / 1000000
        #     + response_from_ai.usage_metadata.candidates_token_count * 3 / 1000000
        # )
        return response_from_ai.text