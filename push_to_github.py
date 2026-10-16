#!/usr/bin/env python3
"""
Automated Python script to push index.html to https://github.com/Lithish13/cgip
Supports two methods:
  1. GitHub REST API (via Personal Access Token - no Git CLI required)
  2. Local Git subprocess automation
"""

import base64
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error

REPO_OWNER = "Lithish13"
REPO_NAME = "cgip"
BRANCH = "main"
FILE_PATH = "index.html"
COMMIT_MESSAGE = "Add gesture-based calculator web app"


def push_via_github_api(token: str, file_path: str = FILE_PATH):
    """Pushes index.html directly to GitHub using Python's standard urllib & GitHub REST API."""
    if not os.path.exists(file_path):
        print(f"[!] Error: '{file_path}' not found in the current directory.")
        sys.exit(1)

    with open(file_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("utf-8")

    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Python-GitHub-Uploader",
        "Content-Type": "application/json",
    }

    # Check if index.html already exists in the repo to fetch its SHA
    sha = None
    try:
        req = urllib.request.Request(f"{api_url}?ref={BRANCH}", headers=headers, method="GET")
        with urllib.request.urlopen(req) as resp:
            existing_data = json.loads(resp.read().decode("utf-8"))
            sha = existing_data.get("sha")
            print(f"[*] Existing '{file_path}' found on GitHub (SHA: {sha[:7]}). Updating file...")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"[*] Creating new file '{file_path}' in {REPO_OWNER}/{REPO_NAME}...")
        else:
            print(f"[!] HTTP Error checking file status: {e.code} {e.reason}")
            print(e.read().decode("utf-8", errors="ignore"))
            sys.exit(1)

    payload = {
        "message": COMMIT_MESSAGE,
        "content": content_b64,
        "branch": BRANCH,
    }
    if sha:
        payload["sha"] = sha

    data = json.dumps(payload).encode("utf-8")
    put_req = urllib.request.Request(api_url, data=data, headers=headers, method="PUT")

    try:
        with urllib.request.urlopen(put_req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            html_url = result.get("content", {}).get("html_url", f"https://github.com/{REPO_OWNER}/{REPO_NAME}")
            print(f"[+] Successfully pushed '{file_path}' to GitHub!")
            print(f"[+] View file: {html_url}")
    except urllib.error.HTTPError as e:
        print(f"[!] Failed to push via GitHub API: {e.code} {e.reason}")
        print(e.read().decode("utf-8", errors="ignore"))
        sys.exit(1)


def push_via_git_cli(file_path: str = FILE_PATH):
    """Fallback method using Python's subprocess module to run Git commands."""
    repo_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}.git"
    commands = [
        ["git", "init"],
        ["git", "branch", "-M", BRANCH],
        ["git", "add", file_path],
        ["git", "commit", "-m", COMMIT_MESSAGE],
    ]
    for cmd in commands:
        subprocess.run(cmd, check=False)

    # Set remote origin (update if already exists)
    res = subprocess.run(["git", "remote", "add", "origin", repo_url], capture_output=True, text=True)
    if res.returncode != 0:
        subprocess.run(["git", "remote", "set-url", "origin", repo_url], check=False)

    print(f"[*] Pulling latest changes from {repo_url}...")
    subprocess.run(["git", "pull", "origin", BRANCH, "--rebase"], check=False)

    print(f"[*] Pushing to {repo_url}...")
    subprocess.run(["git", "push", "-u", "origin", BRANCH], check=True)
    print(f"[+] Successfully pushed to https://github.com/{REPO_OWNER}/{REPO_NAME}")


if __name__ == "__main__":
    print("=== GitHub Python Uploader for Lithish13/cgip ===")
    token = os.environ.get("GITHUB_TOKEN") or input("Enter your GitHub Personal Access Token (or press Enter to use local Git CLI): ").strip()
    if token:
        push_via_github_api(token)
    else:
        push_via_git_cli()
