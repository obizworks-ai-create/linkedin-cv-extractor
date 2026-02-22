import os
import json
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

class NotificationManager:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_WHATSAPP_FROM")
        self.to_number = os.getenv("TWILIO_WHATSAPP_TO")
        
        self.client = None
        if self.account_sid and self.auth_token:
            try:
                # Basic check to see if placeholders were replaced
                if "AC" in self.account_sid and len(self.account_sid) > 30:
                    self.client = Client(self.account_sid, self.auth_token)
            except:
                print("⚠️ Twilio Client failed to initialize. Check credentials.")

    def send_whatsapp(self, message: str):
        if not self.client:
            print("⚠️ Twilio not configured. Message not sent.")
            return
        
        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=self.to_number
            )
            print(f"✅ WhatsApp alert sent! SID: {msg.sid}")
            return msg.sid
        except Exception as e:
            print(f"❌ Failed to send WhatsApp: {e}")
            return None

    def notify_new_reply(self, candidate_name: str, message_snippet: str):
        text = f"🚨 *AI Hiring Agent Alert*\n\nNew reply from *{candidate_name}*:\n\"{message_snippet}\"\n\nCheck your LinkedIn inbox!"
        return self.send_whatsapp(text)
