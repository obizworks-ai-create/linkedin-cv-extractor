import os
import sys
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI

# Load Env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

ckey = os.getenv("CEREBRAS_API_KEY")
print(f"Key: {ckey[:5]}...")

client = OpenAI(api_key=ckey, base_url="https://api.cerebras.ai/v1")

try:
    models = client.models.list()
    print("\nAvailable Models:")
    for m in models.data:
        print(f" - {m.id}")
except Exception as e:
    print(f"Error listing models: {e}")
