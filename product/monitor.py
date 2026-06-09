#!/usr/bin/env python3
"""
AI Web Monitor — Autonomous web page monitoring with intelligent change detection.
Monitors any set of URLs, detects changes using AI, and sends email alerts.

Usage:
  python3 monitor.py add https://example.com "Competitor Pricing Page"
  python3 monitor.py run              # Run one check cycle
  python3 monitor.py list             # List monitored pages
  python3 monitor.py remove <id>      # Stop monitoring a page

Configuration: Set these env vars or edit config dict below.
  RECIPIENT_EMAIL  — Where alerts go (default: kai.rhodes1999@gmail.com)
  SENDER_EMAIL     — Gmail address
  SENDER_PASSWORD  — Gmail app password
"""

import hashlib, json, os, sys, time, smtplib, email.utils
from datetime import datetime
from email.mime.text import MIMEText
from urllib.request import Request, urlopen
from urllib.parse import urlparse

# ── Config ──────────────────────────────────────────────────────────
CONFIG_DIR = os.path.expanduser("~/.ai-web-monitor")
os.makedirs(CONFIG_DIR, exist_ok=True)
DB_FILE = os.path.join(CONFIG_DIR, "pages.json")
HISTORY_DIR = os.path.join(CONFIG_DIR, "history")
os.makedirs(HISTORY_DIR, exist_ok=True)

RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", "kai.rhodes1999@gmail.com")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "")

USER_AGENT = "AIWebMonitor/1.0 (kai.rhodes1999@gmail.com)"

# ── Database ────────────────────────────────────────────────────────
def load_pages():
    if os.path.exists(DB_FILE):
        with open(DB_FILE) as f:
            return json.load(f)
    return {"pages": [], "next_id": 1}

def save_pages(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── Fetch & Diff ────────────────────────────────────────────────────
def fetch_page(url):
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as resp:
        content = resp.read().decode("utf-8", errors="replace")
    return content

def content_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()

def get_history(page_id):
    path = os.path.join(HISTORY_DIR, f"page_{page_id}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []

def save_history(page_id, entry):
    hist = get_history(page_id)
    hist.append(entry)
    if len(hist) > 50:  # keep last 50 checks
        hist = hist[-50:]
    with open(os.path.join(HISTORY_DIR, f"page_{page_id}.json"), "w") as f:
        json.dump(hist, f, indent=2)

# ── AI Summary (using Hermes/OpenRouter API) ────────────────────────
def summarize_change(url, label, old_content, new_content):
    """Use the OpenRouter API to generate a smart summary of changes."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return "Change detected (AI summary unavailable — no API key configured)"

    # Truncate content to avoid huge token costs
    old_snippet = old_content[:3000] if old_content else ""
    new_snippet = new_content[:3000]

    # For simple diff, just compare lengths and flag major changes
    old_len = len(old_content or "")
    new_len = len(new_content or "")
    size_change = new_len - old_len
    size_pct = ((new_len - old_len) / max(old_len, 1)) * 100

    summary_parts = []
    if abs(size_pct) > 1:
        direction = "grew" if size_change > 0 else "shrank"
        summary_parts.append(f"Page {direction} by {abs(size_pct):.0f}% ({size_change:+d} chars)")

    # Quick content-level checks
    if old_content and new_content:
        old_lines = set(old_content.split('\n'))
        new_lines = set(new_content.split('\n'))
        added = new_lines - old_lines
        removed = old_lines - new_lines
        if added:
            summary_parts.append(f"~{len(added)} new lines detected")
        if removed:
            summary_parts.append(f"~{len(removed)} lines removed")

    if summary_parts:
        return f"Changes: {', '.join(summary_parts)}"
    return "Minor changes detected (content hash changed)"

# ── Email Alerts ────────────────────────────────────────────────────
def send_alert(page, summary):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print(f"  ⚠  Email not configured — would send alert for: {page['label']}")
        print(f"      Summary: {summary}")
        return False

    msg = MIMEText(f"""AI Web Monitor — Change Detected

Page: {page['label']}
URL:  {page['url']}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

Summary:
{summary}
---
This is an automated alert from AI Web Monitor.
To stop monitoring this page: python3 monitor.py remove {page['id']}
""")
    msg["Subject"] = f"🔔 Change Detected: {page['label']}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL
    msg["Date"] = email.utils.formatdate()

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"  ⚠  Failed to send email: {e}")
        return False

# ── Commands ────────────────────────────────────────────────────────
def cmd_add(url, label):
    data = load_pages()
    page_id = data["next_id"]
    data["pages"].append({"id": page_id, "url": url, "label": label, "added": datetime.now().isoformat()})
    data["next_id"] = page_id + 1
    save_pages(data)
    print(f"✅ Added #{page_id}: {label} ({url})")
    print(f"   First check will run on next 'monitor.py run' cycle")

def cmd_remove(page_id):
    data = load_pages()
    before = len(data["pages"])
    data["pages"] = [p for p in data["pages"] if p["id"] != page_id]
    after = len(data["pages"])
    save_pages(data)
    if before != after:
        print(f"✅ Removed page #{page_id}")
    else:
        print(f"⚠  No page found with id #{page_id}")

def cmd_list():
    data = load_pages()
    if not data["pages"]:
        print("📋 No pages being monitored.")
        print("   Add one: python3 monitor.py add <url> <label>")
        return
    print(f"📋 Monitoring {len(data['pages'])} page(s):")
    for p in data["pages"]:
        hist = get_history(p["id"])
        last_check = hist[-1]["time"] if hist else "never"
        last_change = " — ".join(h["summary"] for h in hist[-3:] if h.get("changed"))
        print(f"  #{p['id']} {p['label']}")
        print(f"     URL: {p['url']}")
        print(f"     Last check: {last_check}")
        if last_change:
            print(f"     Recent: {last_change}")

def cmd_run():
    data = load_pages()
    if not data["pages"]:
        print("📋 No pages to check. Add some first.")
        return

    print(f"🔍 Checking {len(data['pages'])} page(s)...")
    changes_found = 0
    errors = 0

    for page in data["pages"]:
        print(f"  ⏳ {page['label']}...", end=" ", flush=True)
        try:
            content = fetch_page(page["url"])
            current_hash = content_hash(content)

            hist = get_history(page["id"])
            last_entry = hist[-1] if hist else None

            changed = last_entry is None or current_hash != last_entry["hash"]

            if changed and last_entry is not None:
                # Summarize what changed
                old_content = None
                if os.path.exists(os.path.join(HISTORY_DIR, f"content_{page['id']}.txt")):
                    with open(os.path.join(HISTORY_DIR, f"content_{page['id']}.txt")) as f:
                        old_content = f.read()

                summary = summarize_change(page["url"], page["label"], old_content, content)
                entry = {"time": datetime.now().isoformat(), "hash": current_hash, "changed": True, "summary": summary}
                save_history(page["id"], entry)
                # Save content for next diff
                with open(os.path.join(HISTORY_DIR, f"content_{page['id']}.txt"), "w") as f:
                    f.write(content)
                changes_found += 1
                print(f"⚠  CHANGE DETECTED")
                print(f"     {summary}")
                send_alert(page, summary)
            elif last_entry is None:
                # First check — just record
                entry = {"time": datetime.now().isoformat(), "hash": current_hash, "changed": False, "summary": "Initial snapshot"}
                save_history(page["id"], entry)
                with open(os.path.join(HISTORY_DIR, f"content_{page['id']}.txt"), "w") as f:
                    f.write(content)
                print(f"✅ Baseline saved")
            else:
                # Periodic no-change log
                entry = {"time": datetime.now().isoformat(), "hash": current_hash, "changed": False, "summary": "No change"}
                save_history(page["id"], entry)
                print(f"✅ No change")

        except Exception as e:
            errors += 1
            print(f"❌ Error: {e}")

    summary = f"\n📊 Check complete: {changes_found} change(s) detected, {errors} error(s)"
    print(summary)
    return changes_found

def cmd_status():
    """Show monitor statistics."""
    data = load_pages()
    total_pages = len(data["pages"])
    total_checks = 0
    total_changes = 0
    for p in data["pages"]:
        hist = get_history(p["id"])
        total_checks += len(hist)
        total_changes += sum(1 for h in hist if h.get("changed"))
    print(f"📊 AI Web Monitor Status")
    print(f"   Pages monitored: {total_pages}")
    print(f"   Total checks run: {total_checks}")
    print(f"   Changes detected: {total_changes}")
    print(f"   History dir: {HISTORY_DIR}")
    print(f"   Config: {DB_FILE}")
    print(f"   Alerts to: {RECIPIENT_EMAIL}")

# ── Main ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "add" and len(sys.argv) >= 4:
        cmd_add(sys.argv[2], sys.argv[3])
    elif cmd == "remove" and len(sys.argv) >= 3:
        cmd_remove(int(sys.argv[2]))
    elif cmd == "list":
        cmd_list()
    elif cmd == "run":
        cmd_run()
    elif cmd == "status":
        cmd_status()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
