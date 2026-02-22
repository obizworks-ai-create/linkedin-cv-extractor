import os
import subprocess
import json
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from src.sourcing import SourcingEngine
from src.notifications import NotificationManager
from src.agent import HiringAgent

# Load .env from the backend directory
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

if not os.getenv("CEREBRAS_API_KEY"):
    print("⚠️  WARNING: CEREBRAS_API_KEY not found — AI analysis will fail!")
else:
    print("✅ CEREBRAS_API_KEY loaded successfully.")

app = FastAPI(title="AI Hiring Agent API")

@app.get("/")
def root():
    return {"status": "online", "message": "AI Hiring Agent API is operational", "docs": "/docs"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class SourcingRequest(BaseModel):
    role: str
    location: str = "United States"
    search_depth: int = 10

class RankingRequest(BaseModel):
    role: str
    persona: str

class DeepScrapeRequest(BaseModel):
    role: str
    persona: str

class AnalyzeRequest(BaseModel):
    role: str
    persona: str

class OutreachRequest(BaseModel):
    candidate_id: str
    personalized_message: str

sourcing_engine = SourcingEngine()
notification_manager = NotificationManager()
agent = HiringAgent()

@app.on_event("startup")
async def startup_event():
    print("\n" + "="*50)
    print("🚀 TALENT SCOUT BACKEND STARTING")
    
    # Start background polling for LinkedIn replies (Skip if on Vercel/Serverless)
    if not os.getenv("VERCEL"):
        import threading
        import time
        
        def poll_replies_worker():
            print("🕒 Background Polling Started: Checking for replies every 10 mins...")
            seen_replies_path = Path("seen_replies.json")
            
            while True:
                try:
                    # 1. Load seen IDs
                    seen_ids = set()
                    if seen_replies_path.exists():
                        with open(seen_replies_path, "r") as f:
                            seen_ids = set(json.load(f))
                    
                    # 2. Check for replies
                    print("🔍 Background check for new LinkedIn replies...")
                    threads = sourcing_engine.check_replies()
                    new_ids = []
                    
                    for thread in threads:
                        thread_id = thread.get('threadId') or thread.get('profileUrl')
                        last_msg = thread.get('lastMessage', {})
                        msg_id = last_msg.get('id') or f"{thread_id}_{last_msg.get('timestamp')}"
                        
                        if not last_msg.get('fromMe') and msg_id not in seen_ids:
                            name = thread.get('fullName', 'A candidate')
                            snippet = last_msg.get('text', 'No text')
                            print(f"🚨 New reply from {name}! Sending WhatsApp notification...")
                            notification_manager.notify_new_reply(name, snippet)
                            seen_ids.add(msg_id)
                            new_ids.append(msg_id)
                    
                    # 3. Save seen IDs
                    if new_ids:
                        with open(seen_replies_path, "w") as f:
                            json.dump(list(seen_ids), f)
                            
                except Exception as e:
                    print(f"⚠️ Polling Error: {e}")
                
                # Wait 10 minutes (600 seconds)
                time.sleep(600)

        polling_thread = threading.Thread(target=poll_replies_worker, daemon=True)
        polling_thread.start()
    else:
        print("☁️ Running on Vercel: Background polling thread disabled. Use /check-replies for manual or cron triggers.")

    if os.getenv("CEREBRAS_API_KEY"):
        print("✅ CEREBRAS API KEY: LOADED")
    else:
        print("❌ CEREBRAS API KEY: MISSING")
    print("="*50 + "\n")

def write_status(stage: str, message: str):
    """Write pipeline status to a JSON file for frontend polling."""
    import datetime
    from datetime import UTC
    status = {"stage": stage, "message": message, "timestamp": datetime.datetime.now(UTC).isoformat()}
    try:
        with open("pipeline_status.json", "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2)
    except Exception as e:
        print(f"⚠️ Warning: Could not write status: {e}")

def _run_stage(stage: str, role: str, location: str = "United States", search_depth: int = 10, persona_text: str = None):
    """Run a specific pipeline stage as a subprocess."""
    # Save persona if provided
    if persona_text:
        with open("persona.txt", "w", encoding="utf-8") as f:
            f.write(persona_text)

    # IMMEDIATE STATUS RESET: Prevent frontend from seeing old results
    status_map = {
        "source": ("sourcing", f"Initializing search for '{role}'..."),
        "rank": ("ranking", "Initializing AI Ranking..."),
        "deep-scrape": ("deep_scraping", "Initializing Deep Scrape..."),
        "analyze": ("analyzing", "Initializing Final Analysis...")
    }
    s_stage, s_msg = status_map.get(stage, (stage, f"Starting {stage}..."))
    write_status(s_stage, s_msg)

    cmd = [
        "python", "-m", "src.main",
        "--stage", stage,
        "--role", role,
        "--location", location,
        "--search_depth", str(search_depth),
    ]
    if persona_text:
        cmd += ["--persona", "persona.txt"]

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    with open("analysis.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"\n\n--- Stage: {stage} for {role} ---\n")
        subprocess.Popen(cmd, stdout=log_file, stderr=log_file, env=env)


# ─── STAGE 1: SOURCE ────────────────────────────────────────────────
@app.post("/start-sourcing")
def start_sourcing(req: SourcingRequest):
    try:
        _run_stage("source", req.role, req.location, req.search_depth)
        return {"status": "started", "message": "Sourcing started. Searching LinkedIn for Open-to-Work candidates..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── STAGE 2: RANK ──────────────────────────────────────────────────
@app.post("/start-ranking")
def start_ranking(req: RankingRequest):
    if not os.path.exists("sourced_candidates.json"):
        raise HTTPException(status_code=400, detail="No sourced candidates. Run Sourcing first.")
    try:
        _run_stage("rank", req.role, persona_text=req.persona)
        return {"status": "started", "message": "AI is ranking candidates against your persona..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── STAGE 3: DEEP PROFILE SEARCH (PhantomBuster only) ──────────────
@app.post("/start-deep-scrape")
def start_deep_scrape(req: DeepScrapeRequest):
    if not os.path.exists("ranked_candidates.json"):
        raise HTTPException(status_code=400, detail="No ranked candidates. Run AI Ranking first.")
    try:
        _run_stage("deep-scrape", req.role, persona_text=req.persona)
        return {"status": "started", "message": "Deep scraping top candidate profiles..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── STAGE 4: AI ANALYZE (Final AI assessment) ──────────────────────
@app.post("/start-analyze")
def start_analyze(req: AnalyzeRequest):
    if not os.path.exists("deep_scraped_candidates.json"):
        raise HTTPException(status_code=400, detail="No deep-scraped candidates. Run Deep Profile Search first.")
    try:
        _run_stage("analyze", req.role, persona_text=req.persona)
        return {"status": "started", "message": "Running final AI assessment on deep-scraped profiles..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── DATA ENDPOINTS ─────────────────────────────────────────────────
@app.get("/sourced")
def get_sourced():
    if not os.path.exists("sourced_candidates.json"):
        return {"sourced": []}
    with open("sourced_candidates.json", "r", encoding="utf-8") as f:
        return {"sourced": json.load(f)}

@app.get("/ranked")
def get_ranked():
    if not os.path.exists("ranked_candidates.json"):
        return {"ranked": []}
    with open("ranked_candidates.json", "r", encoding="utf-8") as f:
        return {"ranked": json.load(f)}

@app.get("/deep-scraped")
def get_deep_scraped():
    if not os.path.exists("deep_scraped_candidates.json"):
        return {"deep_scraped": []}
    with open("deep_scraped_candidates.json", "r", encoding="utf-8") as f:
        return {"deep_scraped": json.load(f)}

@app.get("/results")
def get_results():
    if not os.path.exists("results.json"):
        return {"results": []}
    with open("results.json", "r", encoding="utf-8") as f:
        return {"results": json.load(f)}

@app.get("/status")
def get_status(response: Response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    if not os.path.exists("pipeline_status.json"):
        return {"stage": "idle", "message": "No analysis running."}
    with open("pipeline_status.json", "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/send-outreach")
def send_outreach(req: OutreachRequest):
    """Trigger the LinkedIn Message Sender Phantom."""
    try:
        success = sourcing_engine.send_outreach(req.candidate_id, req.personalized_message)
        if success:
            return {"status": "success", "message": f"Message sent to {req.candidate_id}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to launch Phantom")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/generate-message")
def generate_message(candidate_id: str, role: str):
    """Use AI to generate a personalized message based on the assessment."""
    try:
        results_path = Path("results.json")
        candidate = None
        if results_path.exists():
            with open(results_path, "r", encoding="utf-8") as f:
                results = json.load(f)
            candidate = next((c for c in results if c.get('candidate_id') == candidate_id), None)
        if not candidate:
            ds_path = Path("deep_scraped_candidates.json")
            if ds_path.exists():
                with open(ds_path, "r", encoding="utf-8") as f:
                    ds = json.load(f)
                    candidate = next((c for c in ds if c.get('id') == candidate_id), None)
        if not candidate:
            return {"message": f"Hi, I saw your profile for the {role} role and would love to chat!"}
        strengths = candidate.get('role_fit_analysis', {}).get('strengths', [])
        strength = strengths[0] if strengths else "impressive background"
        prompt = f"Write a professional, warm 2-sentence LinkedIn outreach message for a {role} role. Mention their specific strength: {strength}. Keep it under 300 characters."
        resp = agent.client.chat.completions.create(model=agent.model, messages=[{"role": "user", "content": prompt}])
        return {"message": resp.choices[0].message.content.strip()}
    except Exception as e:
        return {"message": f"Hi, I saw your profile for the {role} role and would love to chat!"}

@app.post("/check-replies")
def check_replies():
    """Manual trigger to check for LinkedIn replies and send WhatsApp alerts."""
    try:
        threads = sourcing_engine.check_replies()
        new_replies_count = 0
        for thread in threads:
            last_msg = thread.get('lastMessage', {})
            if not last_msg.get('fromMe'):
                name = thread.get('fullName', 'A candidate')
                snippet = last_msg.get('text', 'No text')
                notification_manager.notify_new_reply(name, snippet)
                new_replies_count += 1
        return {"status": "success", "replies_found": new_replies_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
