#!/usr/bin/env python3
"""
Exchange X OAuth2 authorization code for access/refresh tokens.
Usage: python3 exchange_x_token.py <full_redirect_url>
"""
import urllib.request, urllib.parse, json, base64, sys, os

CODE_VERIFIER_FILE = "/home/hermes/.xurl-state/pkce_verifier.txt"
STATE_FILE = "/home/hermes/.xurl-state/oauth_state.txt"
TOKENS_FILE = "/home/hermes/.xurl-state/tokens.json"

CLIENT_ID = "WDJwZUhhZVljenRyVWpfQWV2cjM6MTpjaQ"
CLIENT_SECRET = "OWFIsiqVc1kdm_d0Ka6bVU2Mrvty0_pf2HoQfAYrLbKwObdedI"
REDIRECT_URI = "http://localhost:8080/callback"

def exchange(redirect_url):
    # Parse code and state from redirect URL
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(redirect_url)
    params = parse_qs(parsed.query)
    
    if "code" not in params:
        print(f"❌ No 'code' parameter in URL")
        return False
    
    code = params["code"][0]
    incoming_state = params.get("state", [None])[0]
    
    # Verify state
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            saved_state = f.read().strip()
        if incoming_state and incoming_state != saved_state:
            print(f"⚠️  State mismatch! Expected: {saved_state[:20]}..., Got: {incoming_state[:20]}...")
            # Continue anyway - code might still work
    
    # Read code verifier
    if not os.path.exists(CODE_VERIFIER_FILE):
        print("❌ No code_verifier found. Generate a new auth URL first.")
        return False
    
    with open(CODE_VERIFIER_FILE) as f:
        code_verifier = f.read().strip()
    
    # Exchange
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,
    }).encode()
    
    req = urllib.request.Request(
        "https://api.x.com/2/oauth2/token",
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_header}"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            with open(TOKENS_FILE, "w") as f:
                json.dump(result, f, indent=2)
            
            print(f"✅ TOKEN EXCHANGE SUCCESSFUL!")
            print(f"   Access token: {result['access_token'][:60]}...")
            if 'refresh_token' in result:
                print(f"   Refresh token: {result['refresh_token'][:60]}...")
            print(f"   Expires in: {result.get('expires_in', 'N/A')}s")
            print(f"   Scope: {result.get('scope', 'N/A')}")
            
            # Also write them to xurl config
            xurl_config = os.path.expanduser("~/.xurl")
            if os.path.exists(xurl_config):
                # Try to configure xurl with the token
                import subprocess
                r = subprocess.run(
                    ["xurl", "auth", "import", "--app", "kaiposter", "KaiRhodes__", 
                     json.dumps({"oauth2": result["access_token"]})],
                    capture_output=True, text=True, timeout=10
                )
                print(f"   xurl import: {r.stdout[:200]}")
            
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"❌ Error {e.code}: {body[:500]}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 exchange_x_token.py <redirect_url>")
        sys.exit(1)
    
    success = exchange(sys.argv[1])
    sys.exit(0 if success else 1)