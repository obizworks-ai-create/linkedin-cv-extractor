import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

pb_key = os.getenv("PHANTOMBUSTER_API_KEY")
if not pb_key:
    print("Error: PHANTOMBUSTER_API_KEY not found in .env")
    exit(1)

url = f"https://api.phantombuster.com/api/v2/agents/fetch-all?key={pb_key}"
try:
    resp = requests.get(url)
    resp.raise_for_status()
    agents = resp.json()
    
    print(f"Found {len(agents)} Phantoms.")
    for agent in agents:
        print(f"ID:{agent.get('id')}|NAME:{agent.get('name')}|TYPE:{agent.get('agent')}")
        
except Exception as e:
    print(f"Error: {e}")
