import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

pb_key = os.getenv("PHANTOMBUSTER_API_KEY")
agent_id = os.getenv("PHANTOM_ID")

headers = {'X-Phantombuster-Key': pb_key, 'Content-Type': 'application/json'}
fetch_url = f"https://api.phantombuster.com/api/v2/agents/fetch?id={agent_id}"
agent_data = requests.get(fetch_url, headers=headers).json()
org_s3 = agent_data.get('orgS3Folder')
agent_s3 = agent_data.get('s3Folder')

if org_s3 and agent_s3:
    s3_url = f"https://phantombuster.s3.amazonaws.com/{org_s3}/{agent_s3}/result.json"
    print(f"Fetching from S3: {s3_url}")
    resp = requests.get(s3_url)
    if resp.status_code == 200:
        data = resp.json()
        print(f"Total items: {len(data)}")
        if data:
            print(f"Sample item keys: {list(data[0].keys())}")
            # Look for timestamp or query
            potential_keys = ['timestamp', 'query', 'searchUrl', 'date', 'addedAt']
            for pk in potential_keys:
                if pk in data[0]:
                    print(f"Found key '{pk}': {data[0][pk]}")
else:
    print("No S3 folder found.")
