#!/usr/bin/env python3
"""
Kai Rhodes Email Outreach Engine
Sends cold emails from kai.rhodes1999@gmail.com to potential clients.
Uses Google OAuth2 refresh tokens for Gmail API access.
"""

import base64, json, os, time, urllib.request, urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── Config ─────────────────────────────────────────────────────────
TOKEN_FILE = "/home/hermes/.hermes/google_token.json"
REFRESH_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_API_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
SENDER = "kai.rhodes1999@gmail.com"

# ── Token Management ───────────────────────────────────────────────
def load_tokens():
    if not os.path.exists(TOKEN_FILE):
        print(f"❌ Token file not found: {TOKEN_FILE}")
        return None
    with open(TOKEN_FILE) as f:
        return json.load(f)

def save_tokens(tokens):
    existing = load_tokens() or {}
    existing.update(tokens)
    with open(TOKEN_FILE, "w") as f:
        json.dump(existing, f, indent=2)

def refresh_access_token(refresh_token, client_id, client_secret):
    """Exchange refresh token for a fresh access token."""
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode()

    req = urllib.request.Request(
        REFRESH_TOKEN_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            access_token = result.get("access_token")
            expires_in = result.get("expires_in", 3600)
            print(f"✅ Token refreshed (expires in {expires_in}s)")
            return access_token
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"❌ Token refresh failed: {e.code} - {body[:200]}")
        return None

def get_access_token():
    """Get a valid access token, refreshing if needed."""
    tokens = load_tokens()
    if not tokens:
        return None
    
    client_id = tokens.get("client_id")
    client_secret = tokens.get("client_secret")
    
    if not client_id or not client_secret:
        print("❌ Token file missing client_id or client_secret")
        return None
    
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    
    if not refresh_token:
        print("❌ No refresh token available")
        return None
    
    # Always refresh since access tokens expire quickly
    access_token = refresh_access_token(refresh_token, client_id, client_secret)
    if access_token:
        save_tokens({
            "access_token": access_token,
            "expiry": time.time() + 3600
        })
    
    return access_token

# ── Sending Email ──────────────────────────────────────────────────
def send_email_via_api(to_email, subject, body_html, body_text=None):
    """Send an email using the Gmail API."""
    access_token = get_access_token()
    if not access_token:
        print(f"❌ Cannot send: no valid access token")
        return False
    
    if not body_text:
        import re
        body_text = re.sub(r'<[^>]+>', '', body_html)
    
    # Build MIME message
    msg = MIMEMultipart('alternative')
    msg['To'] = to_email
    msg['From'] = SENDER
    msg['Subject'] = subject
    
    part1 = MIMEText(body_text, 'plain')
    part2 = MIMEText(body_html, 'html')
    msg.attach(part1)
    msg.attach(part2)
    
    # Encode to base64url
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    
    # Send via Gmail API
    payload = json.dumps({"raw": raw}).encode()
    req = urllib.request.Request(
        GMAIL_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            msg_id = result.get("id", "unknown")
            print(f"✅ Email sent to {to_email} | ID: {msg_id}")
            log_entry = {
                "to": to_email,
                "subject": subject,
                "time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "msg_id": msg_id,
                "status": "sent"
            }
            log_dir = os.path.expanduser("~/.ai-web-monitor/outreach")
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, "sent.jsonl"), "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"❌ Gmail API error {e.code}: {body[:300]}")
        return False
    except Exception as e:
        print(f"❌ Error sending to {to_email}: {e}")
        return False

# ── Campaign Templates ─────────────────────────────────────────────
def pitch_website_chatbot(business_name, contact_name=None):
    """Pitch: Website chatbot for lead capture."""
    name = contact_name or "there"
    biz = business_name or "your business"
    
    subject = f"Quick idea for {biz}"
    body_html = f"""<html><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
<p>Hi {name},</p>
<p>I build AI chatbots for small businesses. Here's what I mean: a smart chat widget on your website that handles FAQs, books appointments, and captures leads — while you sleep.</p>
<p>One client went from missing 60% of their after-hours enquiries to capturing every single one. Total cost: <b>$300, one-time</b>.</p>
<p>No monthly fees. No complicated setup. Just a working chatbot in 48 hours.</p>
<p>Want to see a demo? Reply and I'll send one over.</p>
<p>Best,<br><b>Kai Rhodes</b></p></body></html>"""
    return subject, body_html

def pitch_workflow_automation(business_name, contact_name=None):
    """Pitch: Workflow automation for time savings."""
    name = contact_name or "there"
    biz = business_name or "your business"
    
    subject = f"Automating {biz}'s repetitive tasks"
    body_html = f"""<html><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
<p>Hi {name},</p>
<p>I build custom automations for businesses like {biz}. If your team is doing any of these manually, I can probably automate it:</p>
<ul>
<li>Sending follow-up emails to leads</li>
<li>Entering data from one system into another</li>
<li>Monitoring competitor pricing or content</li>
<li>Generating social media posts or reports</li>
</ul>
<p>Fixed price, typically <b>$100-$400</b>, delivered in 24-72 hours. No subscriptions, no ongoing fees.</p>
<p>Got 2 minutes to tell me what's eating your team's time?</p>
<p>Best,<br><b>Kai Rhodes</b></p></body></html>"""
    return subject, body_html

# ── Main ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 email_outreach.py test")
        print("  python3 email_outreach.py check")
        print("  python3 email_outreach.py send <email> [business_name]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "test":
        print("🧪 Sending test email to self...")
        subject, html = pitch_website_chatbot("Test Business", "Tee")
        success = send_email_via_api(SENDER, subject, html)
        print(f"📬 Result: {'✅ Sent' if success else '❌ Failed'}")
    
    elif cmd == "send":
        to_email = sys.argv[2] if len(sys.argv) > 2 else None
        biz_name = sys.argv[3] if len(sys.argv) > 3 else "your business"
        if not to_email:
            print("❌ No recipient email provided")
            sys.exit(1)
        
        print(f"📧 Sending outreach to {to_email}...")
        subject, html = pitch_website_chatbot(biz_name)
        success = send_email_via_api(to_email, subject, html)
        print(f"📬 Result: {'✅ Sent' if success else '❌ Failed'}")
    
    elif cmd == "check":
        print("🔍 Checking Google OAuth tokens...")
        access_token = get_access_token()
        if access_token:
            print(f"✅ Tokens valid! Access token: {access_token[:30]}...")
        else:
            print("❌ Tokens invalid or expired")
    
    else:
        print(f"Unknown command: {cmd}")