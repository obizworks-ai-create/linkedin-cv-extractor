import os
import requests
from dotenv import load_dotenv
from pathlib import Path

def test_phantombuster():
    print("👻 Deep Testing PhantomBuster Integration...\n")
    
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=env_path)
    
    pb_key = os.getenv("PHANTOMBUSTER_API_KEY")
    pb_id = os.getenv("PHANTOM_ID")

    if not pb_key or not pb_id:
        print("❌ Error: PHANTOMBUSTER_API_KEY or PHANTOM_ID missing in .env")
        return

    headers = {"X-Phantombuster-Key": pb_key, "Content-Type": "application/json"}

    # 1. Test Agent Metadata Access
    print(f"📡 Testing Metadata Access for ID: {pb_id}...")
    url = f"https://api.phantombuster.com/api/v2/agents/fetch?id={pb_id}"
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Metadata Access: SUCCESS")
        print(f"   Agent Name: {data.get('name')}")
        print(f"   Agent Status: {data.get('status') or 'Idle'}")
        
        # 2. Test Argument Fetching (Check if we can read session cookies/search URLs)
        args = data.get('argument')
        if args:
            print(f"✅ Argument Access: SUCCESS (Permissions verified)")
        else:
            print(f"⚠️  Argument Access: EMPTY (Check if agent is configured)")

        # 3. Test S3 Result Access (Check if existing results can be reached)
        org_s3 = data.get('orgS3Folder')
        agent_s3 = data.get('s3Folder')
        if org_s3 and agent_s3:
            s3_url = f"https://phantombuster.s3.amazonaws.com/{org_s3}/{agent_s3}/result.json"
            print(f"📡 Verifying S3 Storage Link: {s3_url[:60]}...")
            s3_resp = requests.get(s3_url)
            if s3_resp.status_code == 200:
                print(f"✅ S3 Data Access: SUCCESS (Stored results are readable)")
            else:
                print(f"ℹ️  S3 Data Access: No current result.json found (Normal if never run)")
        
    elif resp.status_code == 401:
        print(f"❌ Error: API Key is invalid (UNAUTHORIZED)")
    elif resp.status_code == 404:
        print(f"❌ Error: Phantom ID {pb_id} not found in this account")
    else:
        print(f"❌ Error: {resp.status_code} - {resp.text}")

    print("\n🏁 PhantomBuster Verification Complete.")

if __name__ == "__main__":
    test_phantombuster()
