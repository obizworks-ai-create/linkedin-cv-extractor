import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from twilio.rest import Client

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent))

def run_diagnostic():
    load_dotenv(override=True)
    
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_no = os.getenv("TWILIO_WHATSAPP_FROM")
    to_no = os.getenv("TWILIO_WHATSAPP_TO")
    
    print("🧪 --- TWILIO DIAGNOSTIC TEST ---")
    print(f"SID: {sid[:5]}...")
    print(f"From: {from_no}")
    print(f"To: {to_no}")
    
    if not all([sid, token, from_no, to_no]):
        print("❌ Error: Missing credentials in .env")
        return

    try:
        client = Client(sid, token)
        print("⏳ Attempting to send test message...")
        message = client.messages.create(
            body="🚀 Test from your AI Hiring Agent! If you see this, your WhatsApp integration is 100% working.",
            from_=from_no,
            to=to_no
        )
        print(f"✅ Success! Message SID: {message.sid}")
        print(f"📈 Status: {message.status}")
        print("\nNOTE: If you got a 'Success' but no message on your phone, check:")
        print("1. Did you send the 'join ...' code to the Twilio number?")
        print("2. Is your phone connected to the internet?")
        
    except Exception as e:
        print(f"\n❌ TWILIO ERROR: {str(e)}")
        if "not a verified" in str(e).lower():
            print("\n💡 SOLUTION: On a Trial Account, you must verify your phone number in Twilio Console first.")
        elif "sandbox" in str(e).lower() or "not authorized" in str(e).lower():
            print("\n💡 SOLUTION: You must send the 'join' keyword to the Twilio number on WhatsApp first.")

if __name__ == "__main__":
    run_diagnostic()
