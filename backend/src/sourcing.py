import requests
import json
import time
import urllib.parse
import os
from datetime import datetime, UTC
from typing import List, Optional
from .models import CandidateProfile

class SourcingEngine:
    """
    Pure PhantomBuster Sourcing Funnel.
    1. Search (LinkedIn Search Export) -> Up to 10 profiles (Free Tier cap).
    2. Deep Scrape (LinkedIn Profile Scraper) -> Top 3 (Exec Time cap).
    """
    def __init__(self):
        self.pb_key = os.getenv("PHANTOMBUSTER_API_KEY")
        self.pb_search_id = os.getenv("PHANTOM_ID") # Current search phantom
        self.pb_scraper_id = os.getenv("PHANTOM_SCRAPER_ID") # New scraper phantom
        self.pb_message_id = os.getenv("PHANTOM_MESSAGE_SENDER_ID")
        self.pb_inbox_id = os.getenv("PHANTOM_INBOX_SCRAPER_ID")

    def _get_search_state(self):
        """Read search state (per-query history)."""
        if os.path.exists("search_state.json"):
            try:
                with open("search_state.json", "r") as f:
                    return json.load(f)
            except: pass
        return {"history": {}, "queries": {}}

    def _save_search_state(self, role: str, location: str, first_run_iso: str):
        """Save a first-run timestamp for a specific query."""
        state = self._get_search_state()
        topic = f"{role.lower()}|{location.lower()}"
        from datetime import datetime, UTC
        if topic not in state['history']:
            state['history'][topic] = first_run_iso
        state['queries'][topic] = datetime.now(UTC).isoformat()
        with open("search_state.json", "w") as f:
            json.dump(state, f, indent=2)

    def _launch_phantom(self, agent_id: str, payload: dict) -> Optional[str]:
        """Launch a Phantom with retries."""
        headers = {'X-Phantombuster-Key': self.pb_key, 'Content-Type': 'application/json'}
        launch_url = f"https://api.phantombuster.com/api/v2/agents/launch?key={self.pb_key}"
        
        for attempt in range(3):
            try:
                resp = requests.post(launch_url, json=payload, timeout=15)
                resp.raise_for_status()
                container_id = resp.json().get('containerId')
                if container_id:
                    print(f"   ✅ Launch successful. Container ID: {container_id}", flush=True)
                    return container_id
            except Exception as e:
                print(f"   ⚠️ Launch attempt {attempt+1} failed: {e}", flush=True)
                if attempt < 2:
                    time.sleep(10 * (attempt + 1))
        return None

    def search_candidates(self, role: str, location: str, limit: int = 100) -> List[CandidateProfile]:
        """
        Runs the Search Phantom to get a wide net of candidates.
        """
        if not self.pb_key or not self.pb_search_id:
            print("⚠️ Skipping search: PHANTOMBUSTER_API_KEY or PHANTOM_ID not set.")
            return []

        print(f"👻 Launching Search Phantom {self.pb_search_id} for '{role}'...")
        headers = {'X-Phantombuster-Key': self.pb_key, 'Content-Type': 'application/json'}
        
        # 1. Fetch current arguments to keep the session cookie
        fetch_url = f"https://api.phantombuster.com/api/v2/agents/fetch?id={self.pb_search_id}&key={self.pb_key}"
        agent_resp = requests.get(fetch_url, timeout=10)
        agent_resp.raise_for_status()
        agent_data = agent_resp.json()
        
        current_args = agent_data.get('argument', {})
        if not current_args:
            print(f"⚠️ Warning: No arguments found for Phantom {self.pb_search_id}. Search might fail.")
            current_args = {}
        
        if isinstance(current_args, str):
            try: current_args = json.loads(current_args)
            except: current_args = {}
            
        if 'sessionCookie' not in current_args and 'identities' not in current_args:
            print("❌ Error: LinkedIn Session Cookie not found in Phantom arguments. Please check your PhantomBuster dashboard!")
        else:
            print("✅ LinkedIn Session found (via identities/direct).")

        # 2. Launch with new search URL
        # SMART ISOLATION: Check if we've searched this topic before
        state = self._get_search_state()
        topic = f"{role.lower()}|{location.lower()}"
        from datetime import datetime, UTC
        launch_iso = datetime.now(UTC).isoformat()
        
        # Decide on min_timestamp
        if topic in state['history']:
            print(f"   ℹ️ Returning search topic detected. Allowing all candidates found since {state['history'][topic]}")
            min_timestamp = datetime.fromisoformat(state['history'][topic])
        else:
            print(f"   ℹ️ Brand new search topic. Strictly isolating from previous/other searches since {launch_iso}")
            min_timestamp = datetime.fromisoformat(launch_iso)
            self._save_search_state(role, location, launch_iso)

        new_args = current_args.copy()
        
        if 'sessionCookie' not in new_args and 'identities' in new_args and len(new_args['identities']) > 0:
            # Promote the cookie from the first identity to the top level
            # Many Phantoms still look for 'sessionCookie' first.
            new_args['sessionCookie'] = new_args['identities'][0].get('sessionCookie')
            print("   🔑 Promoted session cookie for stability.")

        # BROADENING SEARCH: We put location back into keywords because explicit
        # location facets often trigger LinkedIn's "Guest Preview" mode (3 results).
        broad_keywords = f"{role} {location}"
        encoded_keywords = urllib.parse.quote(broad_keywords)
        search_url = f"https://www.linkedin.com/search/results/people/?keywords={encoded_keywords}&origin=GLOBAL_SEARCH_HEADER"
        
        # CORRECT KEYS for LinkedIn Search Export Phantom:
        new_args['searchType'] = 'linkedInSearchUrl'
        new_args['linkedInSearchUrl'] = search_url
        new_args['numberOfResultsPerLaunch'] = 10 
        new_args['numberOfResultsPerSearch'] = 10
        new_args['noDatabase'] = True
        new_args['removeDuplicateProfiles'] = False
        
        # REMOVE unsupported or conflicting keys
        new_args.pop('location', None)
        new_args.pop('searches', None)
        new_args.pop('csvName', None)
        new_args.pop('spreadsheetUrl', None)
        new_args.pop('searchUrl', None)
        new_args.pop('numberOfResultsPerKeyword', None)
        
        payload = {"id": self.pb_search_id, "argument": new_args}
        print(f"   🚀 Launching High-Volume search: '{broad_keywords}'", flush=True)
        
        # 3. Wait and Fetch - Reverting to standard result.json
        print("   ⚠️ FREE TIER REMINDER: Only the first 10 results will be exported.")
        container_id = self._launch_phantom(self.pb_search_id, payload)
        if not container_id:
            raise Exception("Failed to launch Search Phantom after retries.")

        # 3. Wait and Fetch - Reverting to standard result.json
        result_data = self._wait_for_phantom(container_id, self.pb_search_id)
        if not result_data:
            print("⚠️ No fresh results fetched from PhantomBuster.")
            return []
            
        # Free Tier: Keep all 10 results (don't filter for OTW, just flag them for display)
        return self._parse_pb_results(result_data, only_open_to_work=False, min_timestamp=None)

    def deep_scrape_candidates(self, candidates: List[CandidateProfile], only_open_to_work: bool = False) -> List[CandidateProfile]:
        """
        Runs the Profile Scraper Phantom for specific candidates individually for maximum reliability.
        """
        if not self.pb_key or not self.pb_scraper_id:
            print("ℹ️ Skipping deep scrape: PHANTOM_SCRAPER_ID not set. Using snippets only.")
            return candidates

        # Filter candidates that have valid URLs
        target_candidates = [c for c in candidates if c.id and c.id.startswith("http")]
        if not target_candidates:
            print("ℹ️ No valid LinkedIn URLs found for deep scraping.")
            return candidates

        print(f"👻 Launching Deep Scraper {self.pb_scraper_id} individually for {len(target_candidates)} candidates...")
        
        # 1. Fetch current agent config once
        headers = {'X-Phantombuster-Key': self.pb_key, 'Content-Type': 'application/json'}
        fetch_url = f"https://api.phantombuster.com/api/v2/agents/fetch?id={self.pb_scraper_id}"
        try:
            agent_data = requests.get(fetch_url, headers=headers).json()
            current_args = agent_data.get('argument', {})
            if isinstance(current_args, str):
                try: current_args = json.loads(current_args)
                except: current_args = {}
        except Exception as e:
            print(f"❌ Error fetching Phantom config: {e}")
            return candidates

        all_enriched_candidates = []
        scraped_ids = set()
        
        # 2. Iterate and scrape each candidate
        for idx, candidate in enumerate(target_candidates):
            scrape_start = datetime.utcnow() # capture start time for filtering
            print(f"\n   👤 [{idx+1}/{len(target_candidates)}] Scraping: {candidate.name}", flush=True)
            print(f"      🔗 URL: {candidate.id}", flush=True)
            
            new_args = current_args.copy()
            new_args['spreadsheetUrl'] = candidate.id
            new_args['profileUrls'] = [candidate.id]
            new_args['numberOfProfilesPerLaunch'] = 1
            new_args['numberOfProfilesToScrape'] = 1
            new_args['noDatabase'] = True # Force fresh scrape
            
            payload = {"id": self.pb_scraper_id, "argument": new_args}
            
            # Launch with retries
            container_id = None
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    resp = requests.post("https://api.phantombuster.com/api/v2/agents/launch", headers=headers, json=payload, timeout=15)
                    resp.raise_for_status()
                    data = resp.json()
                    container_id = data.get('containerId')
                    if container_id:
                        break
                    else:
                        print(f"      ⚠️ Launch response missing containerId: {data}", flush=True)
                except Exception as e:
                    print(f"      ⚠️ Launch attempt {attempt+1} failed: {e}", flush=True)
                    if attempt < max_retries - 1:
                        time.sleep(5)

            if not container_id:
                print(f"      ❌ Failed to launch for {candidate.name}. Skipping.", flush=True)
                all_enriched_candidates.append(candidate)
                scraped_ids.add(candidate.id)
                continue

            # Wait and Fetch for this candidate
            result_data = self._wait_for_phantom(container_id, self.pb_scraper_id)
            if result_data:
                # FREE TIER RELIABILITY: For individual deep scrapes, we trust the fresh run.
                # Bypassing strict timestamp check to avoid clock-skew/lag issues.
                # NEW: Pass target_profile_url to ensure we don't pick up stale S3 results for a different candidate.
                parsed = self._parse_pb_results(result_data, only_open_to_work=False, is_deep_scrape=True, target_profile_url=candidate.id)
                if parsed:
                    # Append the enriched candidate
                    enriched = parsed[0]
                    # Retain the ai_score from original if present
                    if hasattr(candidate, 'ai_score'):
                        enriched.ai_score = candidate.ai_score
                    all_enriched_candidates.append(enriched)
                    print(f"      ✅ Successfully enriched {candidate.name}", flush=True)
                else:
                    print(f"      ⚠️ No fresh data returned for {candidate.name} (Might be filtering or S3 lag)", flush=True)
                    all_enriched_candidates.append(candidate)
            else:
                print(f"      ⚠️ Timeout or error fetching results for {candidate.name}", flush=True)
                all_enriched_candidates.append(candidate)
            
            scraped_ids.add(candidate.id)

        # 3. Add back any candidates that weren't in target_candidates
        for c in candidates:
            if c.id not in scraped_ids:
                all_enriched_candidates.append(c)

        return all_enriched_candidates

    def send_outreach(self, profile_url: str, message_text: str) -> bool:
        """
        Launches the Message Sender Phantom for a specific candidate.
        """
        if not self.pb_key or not self.pb_message_id:
            print("⚠️ Outreach failed: PHANTOM_MESSAGE_SENDER_ID not set.")
            return False

        print(f"👻 Launching Messaging Phantom {self.pb_message_id} for {profile_url}...")
        
        # Correct keys for LinkedIn Message Sender:
        # spreadsheetUrl for the recipient, message for the text
        payload = {
            "id": self.pb_message_id,
            "argument": {
                "spreadsheetUrl": profile_url,
                "message": message_text,
                "numberOfProfilesPerLaunch": 1
            }
        }
        
        container_id = self._launch_phantom(self.pb_message_id, payload)
        return bool(container_id)

    def check_replies(self) -> List[dict]:
        """
        Runs the Inbox Scraper and returns recent message threads.
        """
        if not self.pb_key or not self.pb_inbox_id:
            print("⚠️ Inbox Check failed: PHANTOM_INBOX_SCRAPER_ID not set.")
            return []

        print(f"👻 Launching Inbox Scraper Phantom {self.pb_inbox_id}...")
        
        payload = {
            "id": self.pb_inbox_id,
            "argument": {
                "numberOfThreadsToScrape": 20
            }
        }
        
        container_id = self._launch_phantom(self.pb_inbox_id, payload)
        if not container_id: return []

        result_data = self._wait_for_phantom(container_id, self.pb_inbox_id)
        if not result_data: return []

        # Inbox scraper results are usually a list of threads
        threads = result_data if isinstance(result_data, list) else result_data.get('resultObject', [])
        return threads if isinstance(threads, list) else []

    def _wait_for_phantom(self, container_id: str, agent_id: str, expected_filename: str = "result.json") -> any:
        if not container_id:
            return None
            
        headers = {'X-Phantombuster-Key': self.pb_key, 'Content-Type': 'application/json'}
        start_time = time.time()
        max_wait = 900  # 15 minute timeout
        
        print(f"\n   ⏳ Monitoring Phantom container {container_id}...", flush=True)
        
        while True:
            current_elapsed = int(time.time() - start_time)
            if current_elapsed > max_wait:
                print(f"\n   ❌ Polling timeout reached. Phantom is taking too long.", flush=True)
                return None
                
            status_url = f"https://api.phantombuster.com/api/v2/containers/fetch?id={container_id}&key={self.pb_key}"
            try:
                status_resp = requests.get(status_url, timeout=10).json()
                status = status_resp.get('status', 'unknown')
            except Exception as e:
                status = f"request_failed ({str(e)[:20]})"
            
            now_str = datetime.now().strftime("%H:%M:%S")
            print(f"   [{now_str}] Status: {status} (Elapsed: {current_elapsed}s)", flush=True)
            
            if status == 'finished':
                print(f"   ✅ Phantom finished in {current_elapsed}s. Waiting 10s for S3 sync...", flush=True)
                time.sleep(10) # Crucial: Let PhantomBuster sync to S3
                break
            if status == 'error' or 'failed' in status.lower():
                print(f"\n   ❌ PhantomBuster finished with error. Checking logs...", flush=True)
                # Attempt to get console log for better error reporting
                log_url = f"https://api.phantombuster.com/api/v2/containers/fetch-console?id={container_id}&key={self.pb_key}"
                try:
                    log_resp = requests.get(log_url, timeout=10).json()
                    console = log_resp.get('console', '')
                    if "Session cookie not valid" in console or "Session cookie not valid" in str(status_resp):
                        raise Exception("LinkedIn Session Cookie Expired. Please follow the 'Instant Cookie Death' fix in the walkthrough!")
                except Exception as log_e:
                    if "Session Cookie Expired" in str(log_e): raise log_e
                    print(f"   ⚠️ Could not fetch console logs: {log_e}")
                
                print(f"\n   ❌ PhantomBuster finished with error. Details: {status_resp}", flush=True)
                return None
                
            time.sleep(5) # Frequent polling for faster dashboard response
            
        # Download results (Reliable method)
        fetch_url = f"https://api.phantombuster.com/api/v2/agents/fetch?id={agent_id}&key={self.pb_key}"
        agent_resp = requests.get(fetch_url, headers=headers, timeout=10)
        agent_data = agent_resp.json()
        
        # NEW: Check if the API already has the results (fastest fallback)
        if 'resultObject' in agent_data and agent_data['resultObject']:
            # For JSON output, resultObject is often a string that needs parsing
            res_obj = agent_data['resultObject']
            if isinstance(res_obj, str) and (res_obj.startswith('[') or res_obj.startswith('{')):
                try:
                    data = json.loads(res_obj)
                    if data:
                        print("   ✅ Results fetched directly from API.", flush=True)
                        return data
                except: pass
            elif isinstance(res_obj, list) and res_obj:
                print("   ✅ Results fetched directly from API.", flush=True)
                return res_obj

        org_s3 = agent_data.get('orgS3Folder')
        agent_s3 = agent_data.get('s3Folder')
        
        if org_s3 and agent_s3:
            s3_url = f"https://phantombuster.s3.amazonaws.com/{org_s3}/{agent_s3}/{expected_filename}"
            print(f"   ℹ️ Fetching results from S3: {expected_filename} ...", flush=True)
            
            for attempt in range(3):
                try:
                    # Add random query param to bypass S3/Cloudfront cache
                    bust_url = f"{s3_url}?t={int(time.time())}"
                    resp = requests.get(bust_url, timeout=15)
                    if resp.status_code == 200:
                        data = resp.json()
                        size = len(data) if isinstance(data, list) else 1
                        print(f"   ✅ Results fetched from S3. Size: {size}", flush=True)
                        return data
                    else:
                        print(f"   ⚠️ S3 Fetch Attempt {attempt+1} Failed: {resp.status_code}", flush=True)
                except Exception as e:
                    print(f"   ⚠️ S3 Attempt {attempt+1} error: {e}", flush=True)
                
                if attempt < 2:
                    time.sleep(3 * (attempt + 1)) # Exponential backoff
            
            print("   ❌ S3 download failed after 3 attempts.", flush=True)
        else:
            print("   ⚠️ No S3 folder found in Phantom response.", flush=True)
            
        # Last resort fallback: check if agent_data itself has results (sometimes they are present)
        if 'resultObject' in agent_data and agent_data['resultObject']:
            print("   ℹ️ Using fallback data from API response.", flush=True)
            return agent_data['resultObject']
            
        return None

    def _parse_pb_results(self, result_data, only_open_to_work: bool = False, min_timestamp: Optional[datetime] = None, is_deep_scrape: bool = False, target_profile_url: Optional[str] = None) -> List[CandidateProfile]:
        """Parse PhantomBuster results. Raw import mode: filters are disabled unless specifically requested."""
        if not result_data: return []
        if isinstance(result_data, str):
            try: result_data = json.loads(result_data)
            except: return []
            
        candidates = []
        skipped = 0
        # Support both wrapped and unwrapped results
        items = result_data if isinstance(result_data, list) else result_data.get('resultObject', [])
        if not isinstance(items, list): items = [items] if items else []
        print(f"   📦 Parsing {len(items)} items from PhantomBuster result")

        # IDENTITY VERIFICATION (Crucial for Deep Scrape S3 Sync Lag)
        if is_deep_scrape and target_profile_url:
            matched_items = []
            for item in items:
                p_url = item.get('profileUrl') or item.get('general', {}).get('profileUrl')
                # Check for direct match or substring (PhantomBuster URLs often omit trailing slashes or protocols)
                if p_url and (p_url in target_profile_url or target_profile_url in p_url):
                    matched_items.append(item)
                else:
                    print(f"   ⚠️ Identity Mismatch: Result profile ({p_url}) does not match target ({target_profile_url}). Skipping stale S3 data.")
            items = matched_items
            if not items:
                print(f"   ❌ No matching results found for {target_profile_url} in current Phantom output.")

        # Filter by timestamp if provided (bypass if is_deep_scrape=True)
        if min_timestamp and not is_deep_scrape:
            original_count = len(items)
            filtered_items = []
            for item in items:
                ts_str = item.get('timestamp')
                if not ts_str:
                    # If no timestamp, we can't trust it's fresh
                    continue
                try:
                    # PB Format: 2026-02-16T09:58:43.187Z
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00')).replace(tzinfo=None)
                    if ts >= min_timestamp:
                        filtered_items.append(item)
                except Exception as e:
                    print(f"   ⚠️ Error parsing timestamp {ts_str}: {e}")
            
            items = filtered_items
            print(f"   ⏳ Timestamp filter: Kept {len(items)} of {original_count} items (Fresh since {min_timestamp.strftime('%H:%M:%S')})")

        if items and len(items) > 0:
            print(f"   📋 Found {len(items)} candidates in file:")
            for i, item in enumerate(items[:5]):
                name = item.get('name') or item.get('fullName') or 'Unknown'
                headline = item.get('headline') or 'No headline'
                print(f"     [{i+1}] {name}: {headline}")
        
        for i, item in enumerate(items):
            p_url = item.get('profileUrl') or item.get('general', {}).get('profileUrl')
            
            # Try to get full name, or construct it
            name = item.get('name') or item.get('fullName') or item.get('general', {}).get('fullName')
            if not name:
                fname = item.get('firstName') or item.get('general', {}).get('firstName')
                lname = item.get('lastName') or item.get('general', {}).get('lastName')
                if fname and lname:
                    name = f"{fname} {lname}"
                elif fname:
                    name = fname
                else:
                    name = 'Unknown'
            
            if name == 'Unknown':
                print(f"   ⚠️ Skipping item {i}: name is 'Unknown' (Keys: {list(item.keys())[:5]})")
                continue
            headline = item.get('headline') or item.get('general', {}).get('headline', '')
            
            experience_raw = ""
            if 'jobs' in item:
                experience_raw = json.dumps(item['jobs'])
            elif 'general' in item and 'experience' in item['general']:
                experience_raw = item['general']['experience']

            is_otw = True  # Default to True if we're not filtering

            if only_open_to_work:
                # ── OPEN TO WORK DETECTION (only when filtering is ON) ──
                if i == 0: print(f"   ℹ️ OTW Filter: ON")
                intent_keywords = [
                    "opentowork", "#opentowork", "actively seeking", 
                    "seeking opportunities", "available for hire", 
                    "looking for new", "immediate joiner", "open to roles",
                    "actively looking", "open for opportunities"
                ]
                
                is_otw = bool(item.get('isOpenToWork') or item.get('openToWork'))
                
                if not is_otw:
                    about_snippet = item.get('additionalInfo', '').lower()
                    headline_lower = headline.lower()
                    for kw in intent_keywords:
                        if kw in headline_lower or kw in about_snippet:
                            is_otw = True
                            break

                if not is_otw:
                    skipped += 1
                    continue
            else:
                if i == 0: print(f"   ℹ️ OTW Filter: OFF (deep scrape mode — accepting all)")

            candidates.append(CandidateProfile(
                id=p_url or name,
                name=name,
                headline=headline,
                profile_url=p_url,
                experience_text=experience_raw,
                is_open_to_work=is_otw
            ))
        
        if skipped > 0:
            print(f"   🚫 Skipped {skipped} candidates (not Open to Work)")
        print(f"   ✅ Kept {len(candidates)} candidates")
        return candidates
