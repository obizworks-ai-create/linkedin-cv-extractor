import argparse
import json
import os
from dotenv import load_dotenv
from typing import List

# Load env vars from .env file
from pathlib import Path
_backend_dir = Path(__file__).resolve().parent.parent
dotenv_path = _backend_dir / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path=str(dotenv_path), override=True)
else:
    load_dotenv()

if not os.getenv("CEREBRAS_API_KEY"):
    print("⚠️  WARNING: CEREBRAS_API_KEY not found in environment!")

from .models import CandidateProfile
from .sourcing import SourcingEngine
from .agent import HiringAgent

def write_status(stage: str, message: str):
    """Write pipeline status to a JSON file for frontend polling."""
    import datetime
    from datetime import UTC
    status = {"stage": stage, "message": message, "timestamp": datetime.datetime.now(UTC).isoformat()}
    with open("pipeline_status.json", "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)


def stage_source(args):
    """STAGE 1: Source candidates from LinkedIn (Open to Work only)."""
    # Safety: Clear ALL old pipeline data immediately to prevent data leakage
    files_to_clear = [
        "sourced_candidates.json", 
        "ranked_candidates.json", 
        "deep_scraped_candidates.json", 
        "results.json"
    ]
    for f_path in files_to_clear:
        if os.path.exists(f_path):
            try:
                os.remove(f_path)
                with open(f_path, "w", encoding="utf-8") as f:
                    json.dump([], f)
            except Exception as e:
                print(f"⚠️ Warning: Could not clear {f_path}: {e}")

    sourcer = SourcingEngine()

    try:
        write_status("sourcing", f"Searching for '{args.role}' in '{args.location}' (Free Tier: Top 10)...")
        print(f"🌍 STAGE 1: Searching for '{args.role}' in '{args.location}' (Up to 10 results - Free Tier)...")
        candidates_raw = sourcer.search_candidates(role=args.role, location=args.location, limit=args.search_depth)
        print(f"✅ Found {len(candidates_raw)} candidates.")

        sourced_data = [c.model_dump() for c in candidates_raw]
        with open("sourced_candidates.json", "w", encoding="utf-8") as f:
            json.dump(sourced_data, f, indent=2)
        print(f"📁 Saved {len(sourced_data)} sourced candidates to sourced_candidates.json")

        if not candidates_raw:
            write_status("sourcing_done", f"Sourcing complete, but NO candidates found for '{args.role}'. Try a broader role name.")
        else:
            write_status("sourcing_done", f"Sourcing complete. {len(candidates_raw)} candidates found. Click 'Start AI Ranking' to continue.")

    except Exception as e:
        error_msg = str(e)
        if "parallel executions" in error_msg.lower():
            error_msg = "PhantomBuster Error: Maximum parallel executions reached. Please wait a few minutes and try again."
        
        print(f"❌ Sourcing Failed: {error_msg}")
        write_status("error", f"Sourcing Failed: {error_msg}")


def stage_rank(args):
    """STAGE 2: AI ranks the sourced OTW candidates."""
    # Safety: Clear downstream data
    files_to_clear = ["ranked_candidates.json", "deep_scraped_candidates.json", "results.json"]
    for f_path in files_to_clear:
        if os.path.exists(f_path):
            try:
                os.remove(f_path)
                with open(f_path, "w", encoding="utf-8") as f: json.dump([], f)
            except: pass

    if not os.path.exists("sourced_candidates.json"):
        write_status("error", "No sourced candidates found. Run Sourcing first.")
        print("❌ sourced_candidates.json not found. Run sourcing first.")
        return

    with open("sourced_candidates.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    candidates = [CandidateProfile(**c) for c in data]
    print(f"📋 Loaded {len(candidates)} sourced candidates for AI ranking.")

    # Load Persona
    persona_text = None
    if args.persona and os.path.exists(args.persona):
        with open(args.persona, "r", encoding='utf-8') as f:
            persona_text = f.read()
        print(f"🎭 Using Persona from: {args.persona}")

    agent = HiringAgent()

    write_status("ranking", f"AI is scoring {len(candidates)} candidates...")
    print(f"🧠 STAGE 2: AI ranking {len(candidates)} candidates...")
    scored = agent.quick_filter(candidates, role=args.role, limit=len(candidates), ideal_persona=persona_text)

    # Save ALL ranked candidates with their scores
    ranked_data = []
    for score, cand in scored:
        d = cand.model_dump()
        d['ai_score'] = score
        ranked_data.append(d)

    with open("ranked_candidates.json", "w", encoding="utf-8") as f:
        json.dump(ranked_data, f, indent=2)

    # Count how many are >80%
    above_80 = [r for r in ranked_data if r['ai_score'] >= 80]
    print(f"✅ Ranking complete. {len(above_80)} candidates scored ≥80% (out of {len(ranked_data)}).")
    write_status("ranking_done", f"Ranking complete. {len(above_80)} candidates scored ≥80%. Click 'Start Deep Scrape' to continue.")


def stage_deep_scrape(args):
    """STAGE 3: Deep scrape candidates (Scrape only). Supports single URL or batch."""
    # Safety: Clear downstream data
    files_to_clear = ["deep_scraped_candidates.json", "results.json"]
    for f_path in files_to_clear:
        if os.path.exists(f_path):
            try:
                os.remove(f_path)
                with open(f_path, "w", encoding="utf-8") as f: json.dump([], f)
            except: pass

    target_candidates = []
    
    if args.url:
        # Single URL mode
        target_candidates = [CandidateProfile(name="Unknown", profile_url=args.url)]
        print(f"👻 STAGE 3: Individual deep scrape for: {args.url}")
        write_status("deep_scraping", f"Deep scraping profile: {args.url}...")
    else:
        # Batch mode (score >= 80)
        if not os.path.exists("ranked_candidates.json"):
            write_status("error", "No ranked candidates. Run AI Ranking first.")
            print("❌ ranked_candidates.json not found. Run ranking first.")
            return

        with open("ranked_candidates.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Free Tier: Only take top 3 candidates to conserve execution time
        # data is already sorted by score if it comes from agent.quick_filter correctly, 
        # but let's sort again just in case.
        sorted_data = sorted(data, key=lambda x: x.get('ai_score', 0), reverse=True)
        top_candidates = sorted_data[:3]
        
        target_candidates = [CandidateProfile(**{k: v for k, v in c.items() if k != 'ai_score'}) for c in top_candidates]

        if not target_candidates:
            write_status("error", "No qualified candidates found. Nothing to deep scrape.")
            print("❌ No qualified candidates found. Nothing to deep scrape.")
            return
        
        print(f"👻 STAGE 3: Free Tier Mode - Deep scraping TOP {len(target_candidates)} candidates...")
        write_status("deep_scraping", f"Deep scraping top {len(target_candidates)} profiles (Free Tier Cap)...")

    sourcer = SourcingEngine()
    rich_candidates = sourcer.deep_scrape_candidates(target_candidates)

    # NO MERGING: Only keep the results for the current search
    final_data = [c.model_dump() for c in rich_candidates]
    with open("deep_scraped_candidates.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2)

    print(f"✅ Deep scrape complete. {len(rich_candidates)} profiles enriched. Total: {len(final_data)}")
    write_status("deep_scrape_done", f"Deep scrape complete! {len(final_data)} total profiles enriched. Click 'AI Analyze' to continue.")


def stage_analyze(args):
    """STAGE 4: Final AI assessment on deep-scraped candidates."""
    # Safety: Clear own results
    if os.path.exists("results.json"):
        try:
            os.remove("results.json")
            with open("results.json", "w", encoding="utf-8") as f: json.dump([], f)
        except: pass

    if not os.path.exists("deep_scraped_candidates.json"):
        write_status("error", "No deep-scraped candidates. Run Deep Profile Search first.")
        print("❌ deep_scraped_candidates.json not found. Run deep scrape first.")
        return

    with open("deep_scraped_candidates.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    candidates = [CandidateProfile(**c) for c in data]
    print(f"🧠 STAGE 4: Final AI assessment on {len(candidates)} candidates...")

    persona_text = None
    if args.persona and os.path.exists(args.persona):
        with open(args.persona, "r", encoding='utf-8') as f:
            persona_text = f.read()

    agent = HiringAgent()
    write_status("analyzing", f"AI analyzing {len(candidates)} deep-scraped candidates...")

    results = []
    for i, candidate in enumerate(candidates):
        write_status("analyzing", f"Assessing {i+1}/{len(candidates)}: {candidate.name}...")
        print(f"   👉 Assessing: {candidate.name}...")
        assessment = agent.assess_candidate(candidate, role_description=args.role, ideal_persona=persona_text)
        results.append(assessment.model_dump())

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"✨ DONE! {len(results)} candidates analyzed. Saved to results.json")
    write_status("done", f"Analysis complete! {len(results)} candidates assessed.")


def main():
    parser = argparse.ArgumentParser(description="AI Hiring Intelligence Agent")
    parser.add_argument("--stage", type=str, required=True, choices=["source", "rank", "deep-scrape", "analyze"], help="Pipeline stage to run")
    parser.add_argument("--role", type=str, required=True, help="Target job role")
    parser.add_argument("--location", type=str, default="United States", help="Target location")
    parser.add_argument("--search_depth", type=int, default=200, help="Initial candidates to find via search")
    parser.add_argument("--persona", type=str, help="Path to Ideal Candidate Persona text file")
    parser.add_argument("--url", type=str, help="Individual URL to deep scrape")

    args = parser.parse_args()

    if args.stage == "source":
        stage_source(args)
    elif args.stage == "rank":
        stage_rank(args)
    elif args.stage == "deep-scrape":
        stage_deep_scrape(args)
    elif args.stage == "analyze":
        stage_analyze(args)


if __name__ == "__main__":
    main()
