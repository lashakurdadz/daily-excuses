#!/usr/bin/env python3
"""
Refreshes the long-lived Instagram token (they expire after 60 days) and,
if a GH_PAT secret is configured, writes the new token back into the
IG_ACCESS_TOKEN repo secret so the system is fully set-and-forget.

Refreshing returns a NEW token that must be stored - the old one still dies.
So without GH_PAT this script fails loudly on purpose, which makes GitHub
email you, which is your reminder to update the secret by hand.
"""
import os, json, base64, urllib.parse, urllib.request

token = os.environ["IG_ACCESS_TOKEN"]

# 1. refresh
q = urllib.parse.urlencode({"grant_type": "ig_refresh_token", "access_token": token})
with urllib.request.urlopen(f"https://graph.instagram.com/refresh_access_token?{q}",
                            timeout=60) as r:
    data = json.load(r)
new_token = data["access_token"]
print(f"refreshed - new token valid for {data.get('expires_in', 0)//86400} days")

# 2. store it back as the repo secret (needs GH_PAT with repo->secrets write)
pat = os.environ.get("GH_PAT")
repo = os.environ["GITHUB_REPOSITORY"]
if not pat:
    raise SystemExit(
        "GH_PAT not set: the refreshed token could not be saved. "
        "Paste the token printed above... actually don't - tokens must never go in logs. "
        "Add a GH_PAT secret (fine-grained PAT, this repo, Secrets read+write) "
        "to make refresh automatic, or regenerate a token in the Meta dashboard "
        "and update the IG_ACCESS_TOKEN secret manually.")

from nacl import public  # pynacl, installed by the workflow

def gh(path, method="GET", body=None):
    req = urllib.request.Request(f"https://api.github.com{path}", method=method,
        data=json.dumps(body).encode() if body else None,
        headers={"Authorization": f"Bearer {pat}",
                 "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r) if r.status != 204 else {}

key = gh(f"/repos/{repo}/actions/secrets/public-key")
sealed = public.SealedBox(public.PublicKey(base64.b64decode(key["key"])))
enc = base64.b64encode(sealed.encrypt(new_token.encode())).decode()
gh(f"/repos/{repo}/actions/secrets/IG_ACCESS_TOKEN", "PUT",
   {"encrypted_value": enc, "key_id": key["key_id"]})
print("IG_ACCESS_TOKEN secret updated - nothing to do until the next batch")
