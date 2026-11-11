"""Read-only live PR #43 KPI schema drift guard. Never updates schema data."""
import json
import os
import sys
from urllib.parse import quote
from urllib.request import Request, urlopen

REPO = "Mohamedalhindawan/coden-national-dpi"
PR = 43
PATH = "schemas/enterprise/kpi.schema.json"
EXPECTED = "827d5a4d0299ca727be594c56130f1605353bd6a"
API = "https://api.github.com"

def fetch_json(url, token, opener=urlopen):
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "coden-kpi-drift-guard",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = "Bearer " + token
    with opener(Request(url, headers=headers), timeout=20) as response:
        return json.load(response)

def check(token="", fetch=fetch_json):
    pr = fetch(f"{API}/repos/{REPO}/pulls/{PR}", token)
    head = pr["head"]
    sha = head["sha"]
    upstream_repo = head["repo"]["full_name"]
    if not sha or not upstream_repo:
        raise ValueError("Missing upstream PR head SHA or repository")
    content = fetch(
        f"{API}/repos/{upstream_repo}/contents/{quote(PATH)}?ref={quote(sha)}",
        token,
    )
    actual = content["sha"]
    if actual != EXPECTED:
        raise ValueError(
            f"KPI schema drift: expected {EXPECTED}, got {actual}; PR head {sha}"
        )
    return sha, actual

def main():
    try:
        head, blob = check(os.getenv("GITHUB_TOKEN", ""))
    except Exception as exc:
        print(f"KPI upstream schema verification failed: {exc}", file=sys.stderr)
        return 1
    print(f"KPI PR #{PR} schema verified at head {head}, blob {blob}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
