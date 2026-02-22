import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
pb_key = os.getenv("PHANTOMBUSTER_API_KEY")
container_id = "7847324123884650" # The one that finished in 6s

headers = {"X-Phantombuster-Key": pb_key}
url = f"https://api.phantombuster.com/api/v2/containers/fetch-console?id={container_id}"
resp = requests.get(url, headers=headers).json()
print(resp.get("console", "No console output"))
