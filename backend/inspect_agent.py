import os, requests, json
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

key = os.getenv("PHANTOMBUSTER_API_KEY")
aid = os.getenv("PHANTOM_ID")

headers = {"X-Phantombuster-Key": key}
url = f"https://api.phantombuster.com/api/v2/agents/fetch?id={aid}"
resp = requests.get(url, headers=headers)
data = resp.json()

args = data.get("argument", {})
if isinstance(args, str):
    args = json.loads(args)

with open("agent_config.json", "w") as f:
    json.dump(args, f, indent=2)
print("Config saved to agent_config.json")
