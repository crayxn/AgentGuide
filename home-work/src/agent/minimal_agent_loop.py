import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(dotenv_path="../../../.env")

llm = OpenAI(
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_API_KEY"),
    model=os.getenv("LLM_MODEL")
)

llm.responses.create(
    
)

print("HelloWorld")
   