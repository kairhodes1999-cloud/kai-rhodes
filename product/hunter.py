#!/usr/bin/env python3
"""
Opportunity Hunter — Autonomous freelance gig finder.
Scrapes multiple sources for new AI automation/agent gigs and reports them.
Designed to run as a cron job every 2-4 hours.
"""

import json, os, re, subprocess, sys
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.parse import urlencode

CONFIG_DIR = os.path.expanduser("~/.ai-web-monitor")
os.makedirs(CONFIG_DIR, exist_ok=True)
RESULTS_FILE = os.path.join(CONFIG_DIR, "opportunities.json")

# Keywords to search for
KEYWORDS = ["ai agent", "chatbot", "automation", "ai chatbot", "n8n", "make.com", "zapier", 
            "gohighlevel", "llm", "openai", "gpt", "bot", "workflow automation", "web scraper",
            "lead generation", "ai developer", "autonomous agent"]

def search_upwork():
    """Search Upwork for relevant gigs using web scraping."""
    results = []
    for keyword in KEYWORDS[:5]:  # Search top 5 keywords
        try:
            query = urlencode({"q": keyword})
            url = f"https://www.upwork.com/freelance-jobs/search/?{query}"
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="replace")
                # Extract job titles and descriptions from JSON-LD
                if "title" in html:
                    # Simple extraction - look for job titles
                    titles = re.findall(r'"title"\s*:\s*"([^"]+)"', html)
                    for t in titles[:10]:
                        results.append({"source": "Upwork", "title": t, "url": url, "found_at": datetime.now().isoformat()})
        except Exception as e:
            pass
    return results

def search_freelancer():
    """Search Freelancer.com for relevant gigs."""
    results = []
    for keyword in KEYWORDS[:3]:
        try:
            url = f"https://www.freelancer.com/jobs/ai-agents/"
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="replace")
                titles = re.findall(r'"title"\s*:\s*"([^"]+)"', html)
                for t in titles[:5]:
                    results.append({"source": "Freelancer", "title": t, "url": url, "found_at": datetime.now().isoformat()})
        except Exception as e:
            pass
    return results

def search_reddit():
    """Search Reddit for freelance/gig posts."""
    results = []
    subs = ["forhire", "freelance", "jobbit", "ai_agents"]
    for sub in subs:
        try:
            url = f"https://www.reddit.com/r/{sub}/search.json?q=ai+agent+automation&restrict_sr=1&sort=new"
            req = Request(url, headers={"User-Agent": "OpportunityHunter/1.0"})
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                for post in data.get("data", {}).get("children", [])[:5]:
                    pdata = post["data"]
                    results.append({
                        "source": f"Reddit r/{sub}",
                        "title": pdata.get("title", ""),
                        "url": f"https://reddit.com{pdata.get('permalink', '')}",
                        "upvotes": pdata.get("score", 0),
                        "found_at": datetime.now().isoformat()
                    })
        except Exception as e:
            pass
    return results

def save_results(results):
    """Save and deduplicate results."""
    existing = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE) as f:
            existing = json.load(f)
    
    existing_titles = {e["title"] for e in existing}
    new_count = 0
    for r in results:
        if r["title"] not in existing_titles:
            existing.append(r)
            existing_titles.add(r["title"])
            new_count += 1
    
    # Keep last 200
    if len(existing) > 200:
        existing = existing[-200:]
    
    with open(RESULTS_FILE, "w") as f:
        json.dump(existing, f, indent=2)
    
    return new_count, existing

if __name__ == "__main__":
    print(f"🔍 Opportunity Hunter — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_results = []
    
    print("  Searching Reddit...")
    all_results.extend(search_reddit())
    
    # Free upwork search
    print("  Searching Upwork...")
    all_results.extend(search_upwork())
    
    print("  Searching Freelancer...")
    all_results.extend(search_freelancer())
    
    new_count, all_opps = save_results(all_results)
    
    print(f"\n📊 Found {len(all_results)} opportunities ({new_count} new)")
    
    # Show top opportunities
    recent = sorted(all_opps, key=lambda x: x.get("found_at", ""), reverse=True)[:10]
    if recent:
        print("\n🎯 Recent Opportunities:")
        for opp in recent[:5]:
            print(f"  • [{opp['source']}] {opp['title'][:80]}")
            print(f"    {opp['url']}")
    
    # Generate summary for status output
    print(f"\n---END---")
    print(f"Total tracked: {len(all_opps)} | New this run: {new_count}")
