import os
import requests
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

def check_health():
    print("🚀 Starting Backend & API Diagnostics...\n")
    
    # 1. Check .env existence
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        print("❌ CRITICAL: .env file not found in backend directory!")
        return
    
    load_dotenv(dotenv_path=env_path)
    print(f"✅ .env file found at {env_path}")

    # 2. Check API Keys Presence
    keys = {
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
        "PHANTOMBUSTER_API_KEY": os.getenv("PHANTOMBUSTER_API_KEY"),
        "PHANTOM_ID": os.getenv("PHANTOM_ID"),
        "PHANTOM_SCRAPER_ID": os.getenv("PHANTOM_SCRAPER_ID")
    }

    for key_name, value in keys.items():
        if value:
            # Mask key for display
            masked = value[:6] + "..." + value[-4:] if len(value) > 10 else "SET"
            print(f"✅ {key_name}: {masked}")
        else:
            print(f"❌ {key_name}: NOT FOUND")

    # 3. Test Groq API
    if keys["GROQ_API_KEY"]:
        try:
            print("\n🧠 Testing Groq API...")
            client = Groq(api_key=keys["GROQ_API_KEY"])
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "Hello, are you alive? Answer in 1 word."}],
                max_tokens=10
            )
            print(f"✅ Groq Response: {completion.choices[0].message.content.strip()}")
        except Exception as e:
            print(f"❌ Groq API Error: {e}")

    # 4. Test PhantomBuster API
    if keys["PHANTOMBUSTER_API_KEY"]:
        try:
            print("\n👻 Testing PhantomBuster API...")
            headers = {"X-Phantombuster-Key": keys["PHANTOMBUSTER_API_KEY"]}
            
            # Check Search Phantom
            if keys["PHANTOM_ID"]:
                url = f"https://api.phantombuster.com/api/v2/agents/fetch?id={keys['PHANTOM_ID']}"
                resp = requests.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    print(f"✅ Search Phantom Found: {data.get('name')} (Status: {data.get('status')})")
                else:
                    print(f"❌ Search Phantom Error: {resp.status_code} - {resp.text}")
            
            # Check Scraper Phantom
            if keys["PHANTOM_SCRAPER_ID"]:
                url = f"https://api.phantombuster.com/api/v2/agents/fetch?id={keys['PHANTOM_SCRAPER_ID']}"
                resp = requests.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    print(f"✅ Scraper Phantom Found: {data.get('name')} (Status: {data.get('status')})")
                else:
                    print(f"❌ Scraper Phantom Error: {resp.status_code} - {resp.text}")
                    
        except Exception as e:
            print(f"❌ PhantomBuster API Error: {e}")

    print("\n🏁 Health check complete.")

if __name__ == "__main__":
    check_health()
