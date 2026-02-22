import os
import json
import time
from datetime import datetime, UTC
from typing import List, Optional
from apify_client import ApifyClient
from .models import CandidateProfile

class SourcingEngine:
    """
    Apify-powered Sourcing Funnel.
    1. Search (LinkedIn People Search Scraper) -> Sourcing.
    2. Profile Scrape (LinkedIn Profile Scraper) -> Deep Scrape.
    3. Messaging (Send DM for LinkedIn) -> Outreach.
    4. Inbox (LinkedIn Unread Messages Scraper) -> Notifications.
    """
    def __init__(self):
        self.api_token = os.getenv("APIFY_API_TOKEN")
        self.client = ApifyClient(self.api_token) if self.api_token else None
        
        # Actor IDs (Using verified reliable actors)
        self.search_actor = "robotic_tyke/linkedin-people-search-scraper"
        self.profile_actor = "lexis/linkedin-profile-scraper"
        self.message_actor = "addeus/send-dm-for-linkedin"
        self.inbox_actor = "addeus/linkedin-unread-messages-scraper"

    def search_candidates(self, role: str, location: str, limit: int = 10) -> List[CandidateProfile]:
        """
        Runs the Apify Search Actor to find candidates.
        """
        if not self.client:
            print("⚠️ Skipping search: APIFY_API_TOKEN not set.")
            return []

        print(f"🚀 Launching Apify Search for '{role}' in '{location}'...")
        
        # Prepare search keywords
        # We explicitly add "Open to Work" to the search query if possible, 
        # but the actor also has its own filters.
        search_query = f"{role} {location}"
        
        run_input = {
            "queries": [search_query],
            "limit": limit,
            "proxy": { "useApifyProxy": True },
            # Some actors allow a direct "open to work" filter, 
            # if not, we filter the results in the parser.
        }

        try:
            run = self.client.actor(self.search_actor).call(run_input=run_input)
            print(f"✅ Search complete. Fetching results...")
            
            candidates = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                name = item.get("name") or item.get("fullName") or "Unknown"
                headline = item.get("headline") or ""
                profile_url = item.get("url") or item.get("profileUrl")
                
                # Basic OTW detection from search results
                is_otw = "open to work" in headline.lower() or item.get("isOpenToWork", False)
                
                candidates.append(CandidateProfile(
                    id=profile_url or name,
                    name=name,
                    headline=headline,
                    profile_url=profile_url,
                    experience_text="", # Will be filled by deep scrape
                    is_open_to_work=is_otw
                ))
            
            print(f"✅ Found {len(candidates)} candidates.")
            return candidates

        except Exception as e:
            print(f"❌ Apify Search Error: {e}")
            return []

    def deep_scrape_candidates(self, candidates: List[CandidateProfile], only_open_to_work: bool = False) -> List[CandidateProfile]:
        """
        Enriches candidates using the Apify Profile Scraper.
        """
        if not self.client or not candidates:
            return candidates

        valid_urls = [c.profile_url for c in candidates if c.profile_url]
        if not valid_urls:
            return candidates

        print(f"🚀 Deep Scraping {len(valid_urls)} profiles via Apify...")
        
        run_input = {
            "urls": valid_urls,
            "proxy": { "useApifyProxy": True }
        }

        try:
            run = self.client.actor(self.profile_actor).call(run_input=run_input)
            
            enriched_data = {}
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                url = item.get("url") or item.get("profileUrl")
                if url:
                    enriched_data[url] = item

            results = []
            for c in candidates:
                if c.profile_url in enriched_data:
                    data = enriched_data[c.profile_url]
                    
                    # Update candidate with full data
                    c.headline = data.get("headline") or c.headline
                    c.experience_text = json.dumps(data.get("experience", []))
                    c.is_open_to_work = data.get("isOpenToWork", False) or "open to work" in (data.get("summary") or "").lower()
                    
                    if only_open_to_work and not c.is_open_to_work:
                        continue # Skip if we only want OTW and this one isn't
                        
                results.append(c)
                
            return results

        except Exception as e:
            print(f"❌ Apify Deep Scrape Error: {e}")
            return candidates

    def send_outreach(self, profile_url: str, message_text: str) -> bool:
        """
        Sends a LinkedIn DM using Apify.
        """
        if not self.client:
            print("⚠️ Outreach failed: APIFY_API_TOKEN not set.")
            return False

        print(f"✉️ Sending Apify Outreach to {profile_url}...")
        
        run_input = {
            "recipientUrl": profile_url,
            "message": message_text,
            "proxy": { "useApifyProxy": True }
        }

        try:
            self.client.actor(self.message_actor).call(run_input=run_input)
            print(f"✅ Message sent successfully.")
            return True
        except Exception as e:
            print(f"❌ Apify Message Error: {e}")
            return False

    def check_replies(self) -> List[dict]:
        """
        Checks for unread LinkedIn messages using Apify.
        """
        if not self.client:
            return []

        print(f"🔔 Checking for new replies via Apify...")
        
        try:
            run = self.client.actor(self.inbox_actor).call()
            
            replies = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                replies.append({
                    "from": item.get("senderName"),
                    "text": item.get("lastMessage"),
                    "threadUrl": item.get("threadUrl")
                })
            return replies
        except Exception as e:
            print(f"❌ Apify Inbox Error: {e}")
            return []
