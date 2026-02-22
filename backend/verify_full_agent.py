import os
import json
import time
from dotenv import load_dotenv
from src.sourcing import SourcingEngine
from src.agent import HiringAgent
from src.models import CandidateProfile

# Load environment variables
load_dotenv()

def run_full_verification():
    print("🚀 STARTING AGENT VERIFICATION 🚀")
    print("--------------------------------------------------")

    # 1. Setup
    print("🔧 Setting up Source Engine and AI Agent...")
    sourcer = SourcingEngine()
    agent = HiringAgent(model="llama3.1-8b") # Use 8b model as 70b is unavailable
    
    # Check keys
    if not os.getenv("PHANTOM_ID"): print("❌ Error: PHANTOM_ID not found"); return
    if not os.getenv("PHANTOM_SCRAPER_ID"): print("❌ Error: PHANTOM_SCRAPER_ID not found"); return
    if not os.getenv("CEREBRAS_API_KEY"): print("❌ Error: CEREBRAS_API_KEY not found"); return

    # 2. Sourcing (Simulated or Real)
    print("\n🌍 PHASE 1: Sourcing Candidates (Limit 2)...")
    # We will use a real search but with a very small limit to be fast
    # NOTE: PhantomBuster search usually returns min 10, so we'll just slice the result
    try:
        # candidates = sourcer.search_candidates(role="Software Engineer", location="Remote", limit=2)
        # To save time and avoid re-triggering a long phantom launch, let's look for existing sourced_candidates.json
        if os.path.exists("sourced_candidates.json"):
            print("   ℹ️ Loading from 'sourced_candidates.json' to skip Phantom Search wait...")
            with open("sourced_candidates.json", "r") as f:
                data = json.load(f)
                candidates = [CandidateProfile(**c) for c in data][:2] # Take first 2
        else:
            print("   ⚠️ No cache found. This might take 3-5 mins...")
            candidates = sourcer.search_candidates(role="Software Engineer", location="Remote", limit=5)
            candidates = candidates[:2]
        
        print(f"   ✅ Sourced {len(candidates)} candidates for testing.")
        for c in candidates:
            print(f"      - {c.name} ({c.headline[:30]}...)")
            
    except Exception as e:
        print(f"   ❌ Sourcing Failed: {e}")
        return

    # 3. Deep Scraping
    print("\n🕵️ PHASE 2: Deep Scraping (Real Test)...")
    # This is the critical part that was failing or slow
    try:
        print(f"   👻 Sending {len(candidates)} candidates to Profile Scraper...")
        # We need to make sure we're sending candidates with correct URLs
        valid_candidates = [c for c in candidates if c.profile_url and "linkedin.com" in c.profile_url]
        
        if not valid_candidates:
            print("   ❌ No valid LinkedIn URLs to scrape.")
            return

        # Perform the actual scrape
        # NOTE: This will take time (approx 1-2 mins per candidate)
        rich_candidates = sourcer.deep_scrape_candidates(valid_candidates)
        
        print(f"   ✅ Deep Scrape Complete.")
        for c in rich_candidates:
            experience_len = len(c.experience_text) if c.experience_text else 0
            print(f"      - {c.name}: Experience Length = {experience_len} chars")
            if experience_len < 50:
                print("        ⚠️ Warning: Low experience data. Scraping might have been blocked or empty.")

    except Exception as e:
        print(f"   ❌ Deep Scraping Failed: {e}")
        # Print detailed traceback if possible, but keep it simple for now
        import traceback
        traceback.print_exc()
        return

    # 4. AI Analysis
    print("\n🧠 PHASE 3: AI Analysis (Cerebras)...")
    try:
        persona = "A software engineer with Python and React experience, open to startup culture."
        print(f"   🎭 Analyzing against persona: '{persona}'...")
        
        for c in rich_candidates:
            print(f"   👉 Assessing {c.name}...")
            assessment = agent.assess_candidate(c, role_description="Software Engineer", ideal_persona=persona)
            print(f"      ✅ Score: {assessment.overall_score}/100")
            print(f"      ✅ Tier: {assessment.tier}")
            print(f"      ✅ Summary: {assessment.reasoning_summary[:100]}...")

    except Exception as e:
        print(f"   ❌ AI Analysis Failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n--------------------------------------------------")
    print("✅ VERIFICATION COMPLETE: ALL SYSTEMS GO")

if __name__ == "__main__":
    run_full_verification()
