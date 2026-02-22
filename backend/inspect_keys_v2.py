import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

pb_key = os.getenv("PHANTOMBUSTER_API_KEY")
search_id = os.getenv("PHANTOM_ID")

headers = {'X-Phantombuster-Key': pb_key, 'Content-Type': 'application/json'}
url = f"https://api.phantombuster.com/api/v2/agents/fetch?id={search_id}"
resp = requests.get(url, headers=headers)
data = resp.json()

args = data.get('argument')
if isinstance(args, str):
    args = json.loads(args)

if args:
    print("--- FULL ARGUMENT KEYS ---")
    for k in sorted(args.keys()):
        print(f"'{k}'")
    
    # Also check specific interesting values
    print("\n--- CRITICAL VALUES ---")
    print(f"sessionCookie: {'[PRESENT]' if 'sessionCookie' in args else '[MISSING]'}")
    print(f"linkedInSearchUrl: {args.get('linkedInSearchUrl', '[MISSING]')}")
    print(f"spreadsheetUrl: {args.get('spreadsheetUrl', '[MISSING]')}")
else:
    print("No arguments found.")
