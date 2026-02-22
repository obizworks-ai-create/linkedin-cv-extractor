import os
import sys
import json
from dotenv import load_dotenv
from pathlib import Path

# Setup paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.sourcing import SourcingEngine
from src.models import CandidateProfile

# Load Env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

def test_scraping():
    print("🧪 TEST: Launching Real Scraping Job on PhantomBuster...")
    
    # 1. Check ID
    scraper_id = os.getenv("PHANTOM_SCRAPER_ID")
    if not scraper_id:
        print("❌ SKIPPED: PHANTOM_SCRAPER_ID not set.")
        return

    # 2. Mock Candidate (Bill Gates)
    # Using a public figure ensures we don't violate privacy of random people for a test
    dummy = CandidateProfile(
        id="bill-gates",
        name="Bill Gates", 
        headline="Co-chair, Bill & Melinda Gates Foundation",
        profile_url="https://www.linkedin.com/in/williamhgates" 
    )

    engine = SourcingEngine()
    
    try:
        print(f"👻 Sending Bill Gates ({dummy.profile_url}) to PhantomBuster...")
        print("   (This typically takes 1-2 minutes to execute on their servers)")
        
        results = engine.deep_scrape_candidates([dummy])
        
        if not results:
            print("❌ No results returned.")
            exit(1)
            
        gates = results[0]
        print("\n✅ SCRAPE SUCCESSFUL!")
        print(f"Name: {gates.name}")
        print(f"Headline: {gates.headline}")
        print(f"Experience Data Length: {len(gates.experience_text)} chars")
        print("Snippet of Experience (First 200 chars):")
        print(f"{gates.experience_text[:200]}...")
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scraping()
