import os
import sys
import requests
from dotenv import load_dotenv
from pathlib import Path

# Fix path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.agent import HiringAgent
from src.sourcing import SourcingEngine
from src.models import CandidateProfile

# Load Env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

def print_status(step, status, message):
    icon = "✅" if status else "❌"
    print(f"{icon} [{step}] {message}")

def verify_pipeline():
    print("🔍 STARING DEEP SYSTEM VERIFICATION...\n")
    
    # 1. Environment Variables
    ckey = os.getenv("CEREBRAS_API_KEY")
    pkey = os.getenv("PHANTOMBUSTER_API_KEY")
    pid = os.getenv("PHANTOM_ID")
    sid = os.getenv("PHANTOM_SCRAPER_ID")
    
    print_status("ENV", bool(ckey), f"Cerebras Key: {'Found' if ckey else 'MISSING'}")
    print_status("ENV", bool(pkey), f"PhantomBuster Key: {'Found' if pkey else 'MISSING'}")
    print_status("ENV", bool(pid), f"Search Phantom ID: {pid if pid else 'MISSING'}")
    print_status("ENV", bool(sid), f"Scraper Phantom ID: {sid if sid else 'MISSING'}")

    if not all([ckey, pkey, pid, sid]):
        print("\n❌ CRITICAL: Missing configuration. Aborting.")
        return

    # 2. Verify Cerebras Connectivity
    print("\n👉 Testing Cerebras AI...")
    try:
        agent = HiringAgent(model="llama3.1-8b")
        resp = agent.client.chat.completions.create(
            model="llama3.1-8b",
            messages=[{"role": "user", "content": "Ping"}],
            max_tokens=5
        )
        print_status("AI", True, f"Cerebras Responded: {resp.choices[0].message.content}")
    except Exception as e:
        print_status("AI", False, f"Cerebras Failed: {e}")

    # 3. Verify PhantomBuster Agents
    print("\n👉 Testing PhantomBuster Connectivity...")
    headers = {'X-Phantombuster-Key': pkey, 'Content-Type': 'application/json'}
    
    # Check Search Agent
    try:
        url = f"https://api.phantombuster.com/api/v2/agents/fetch?id={pid}"
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            name = res.json().get('name', 'Unknown')
            print_status("PB-Search", True, f"Found Search Agent: '{name}'")
        else:
            print_status("PB-Search", False, f"Could not fetch Agent {pid}. Status: {res.status_code}")
    except Exception as e:
        print_status("PB-Search", False, f"Error: {e}")

    # Check Scraper Agent
    try:
        url = f"https://api.phantombuster.com/api/v2/agents/fetch?id={sid}"
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            name = res.json().get('name', 'Unknown')
            print_status("PB-Scrape", True, f"Found Scraper Agent: '{name}'")
        else:
            print_status("PB-Scrape", False, f"Could not fetch Agent {sid}. Status: {res.status_code}")
    except Exception as e:
        print_status("PB-Scrape", False, f"Error: {e}")

    # 4. Mock Full Flow Check
    print("\n👉 Simulating Data Flow...")
    try:
        # Create a mock candidate
        mock_cand = CandidateProfile(
            id="mock-1", 
            name="Test User", 
            headline="Senior Python Developer", 
            profile_url="http://linkedin.com/in/test"
        )
        
        # Test Quick Filter (AI)
        print("   Testing AI Filter logic...")
        agent.quick_filter([mock_cand], role="Developer", limit=1)
        print_status("Flow-Filter", True, "AI Filter logic executed successfully")

        # Test Assessment (AI)
        print("   Testing AI Assessment logic...")
        res = agent.assess_candidate(mock_cand, role_description="Python Developer")
        print_status("Flow-Assess", True, f"AI Assessment generated score: {res.overall_score}")
        
    except Exception as e:
        print_status("Flow", False, f"Logic Simulation Failed: {e}")

    print("\n✅ VERIFICATION COMPLETE.")

if __name__ == "__main__":
    verify_pipeline()
