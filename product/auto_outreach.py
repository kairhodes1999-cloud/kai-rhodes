#!/usr/bin/env python3
"""
Autonomous Email Outreach Pipeline — runs via cron, sends daily batch.
This script sends 5-10 targeted outreach emails per run from kai.rhodes1999@gmail.com.
Designed to run once daily. Keeps track of who's been contacted.
"""
import json, os, sys
sys.path.insert(0, '/home/hermes/kai-rhodes-landing/product')
from email_outreach import send_email_via_api

LEADS_FILE = os.path.expanduser("~/.ai-web-monitor/outreach/leads.json")
SENT_LOG = os.path.expanduser("~/.ai-web-monitor/outreach/sent.jsonl")
DAILY_LIMIT = 8  # Max emails per run

# Lead database — businesses globally that need AI automation
LEADS = [
    # USA
    ("info@example-plumber.com", "Example Plumbing", "USA"),
    # Canada
    ("info@example-canada.ca", "Example Services", "Canada"),
    # Australia
    ("info@example-au.com.au", "Example AU", "Australia"),
]

def load_sent():
    sent = set()
    if os.path.exists(SENT_LOG):
        with open(SENT_LOG) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    sent.add(entry.get("to", ""))
                except: pass
    return sent

if __name__ == "__main__":
    print(f"📧 Autonomous Outreach Pipeline")
    print(f"   Time: {__import__('time').strftime('%Y-%m-%d %H:%M:%S UTC', __import__('time').gmtime())}")
    
    # For now, just log that we're ready — leads will be populated as found
    print(f"   Status: Pipeline ready, waiting for lead database")
    print(f"   Sents log exists: {os.path.exists(SENT_LOG)}")
    
    # Count sent
    if os.path.exists(SENT_LOG):
        with open(SENT_LOG) as f:
            count = sum(1 for _ in f)
        print(f"   Total sent to date: {count}")
    
    print(f"   Next step: Populate leads.json with target businesses")