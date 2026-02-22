import requests
import json

url = "https://phantombuster.s3.amazonaws.com/ZjBv3WxUg3M/gCZDgi70ZEkbVVIpvBGzGg/result.json"
resp = requests.get(url)
data = resp.json()

print(f"Total items: {len(data)}")
pakistan_items = [item for item in data if "pakistan" in str(item).lower()]
print(f"Items mentioning 'pakistan': {len(pakistan_items)}")

for i, item in enumerate(pakistan_items):
    print(f"\n--- Item {i} ---")
    print(f"Name: {item.get('fullName')}")
    print(f"Headline: {item.get('headline')}")
    print(f"Timestamp: {item.get('timestamp')}")
    print(f"isOpenToWork: {item.get('isOpenToWork')}")
    print(f"openToWork: {item.get('openToWork')}")
    print(f"Query: {item.get('query')}")
