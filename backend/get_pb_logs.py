import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

pb_key = os.getenv("PHANTOMBUSTER_API_KEY")
container_id = "8984389620953471" # From logs

headers = {'X-Phantombuster-Key': pb_key, 'Content-Type': 'application/json'}
url = f"https://api.phantombuster.com/api/v2/containers/fetch-console?id={container_id}"
resp = requests.get(url, headers=headers)
data = resp.json()

print(data.get('console'))
