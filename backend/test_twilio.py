import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent))

from src.notifications import NotificationManager

def test_twilio_init():
    load_dotenv(override=True)
    nm = NotificationManager()
    if nm.client:
        print("✅ Twilio successfully initialized with your credentials!")
        print(f"   From: {nm.from_number}")
        print(f"   To:   {nm.to_number}")
    else:
        print("❌ Twilio failed to initialize. Check your SID and Token in .env.")

if __name__ == "__main__":
    test_twilio_init()
