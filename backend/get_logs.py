import os, requests
key = os.getenv("PHANTOMBUSTER_API_KEY")
cid = "1763564856598987"
headers = {"X-Phantombuster-Key": key}
resp = requests.get(f"https://api.phantombuster.com/api/v2/containers/fetch-console?id={cid}", headers=headers)
print(resp.json().get("console", "No console log found"))
