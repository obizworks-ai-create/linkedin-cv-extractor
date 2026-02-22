import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

pb_key = os.getenv("PHANTOMBUSTER_API_KEY")
if not pb_key:
    print("Error: PHANTOMBUSTER_API_KEY not found in .env")
    exit(1)

print(f"Using API Key: {pb_key[:5]}...{pb_key[-5:]}")

url = f"https://api.phantombuster.com/api/v2/agents/fetch-all?key={pb_key}"
try:
    resp = requests.get(url)
    resp.raise_for_status()
    agents = resp.json()
    
    print(f"\nFound {len(agents)} Phantoms:")
    with open("phantom_ids.txt", "w") as f:
        f.write(f"Found {len(agents)} Phantoms:\n")
        for agent in agents:
            aid = agent.get('id')
            name = agent.get('name')
            output = f"ID:{aid}|NAME:{name}"
            print(output)
            f.write(output + "\n")
    print("\nFull list saved to phantom_ids.txt")
        
except Exception as e:
    print(f"Error fetching phantoms: {e}")
    if hasattr(e, 'response') and e.response:
        print(f"Response: {e.response.text}")
