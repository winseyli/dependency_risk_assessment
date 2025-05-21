import os
import re
import yaml
import json
import requests
from packaging.version import parse as parse_version

# Environment variables
GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO = os.environ["GITHUB_REPOSITORY"]
PR_NUMBER = os.environ["PR_NUMBER"]

# Headers for GitHub API
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

# Load risk level mapping from YAML
with open(".github/risk-levels.yaml", "r") as f:
    risks = yaml.safe_load(f)

# Fetch PR info
pr_url = f"{GITHUB_API}/repos/{REPO}/pulls/{PR_NUMBER}"
pr_data = requests.get(pr_url, headers=headers).json()

# Get PR title
title = pr_data.get("title", "")
print(f"Detected PR title: {title}")

# Extract dependency name and versions
match = re.match(r"Bump ([\w\.\-:]+) from ([\d\.]+) to ([\d\.]+)", title)
if not match:
    print("⚠️ Unable to parse PR title.")
    exit(0)

dep, from_version_str, to_version_str = match.groups()
from_version = parse_version(from_version_str)
to_version = parse_version(to_version_str)

# Determine version difference type
def get_version_diff_level(old, new):
    if new.major > old.major:
        return "major"
    elif new.minor > old.minor:
        return "minor"
    elif new.micro > old.micro:
        return "patch"
    return "none"

version_diff = get_version_diff_level(from_version, to_version)
print(f"Version diff: {version_diff} ({from_version} → {to_version})")

# Determine base risk from YAML
risk_levels = ["low", "medium", "high"]
base_risk = "low"
for level in reversed(risk_levels):  # Start from high
    if dep in risks.get(level, []):
        base_risk = level
        break

# Downgrade risk if it's just a patch bump
if version_diff == "patch" and base_risk != "low":
    index = risk_levels.index(base_risk)
    downgraded_risk = risk_levels[max(0, index - 1)]
    print(f"Downgrading risk from {base_risk} to {downgraded_risk} due to patch bump")
    base_risk = downgraded_risk

# Apply label
label = f"risk: {base_risk}"
print(f"Applying label: {label}")

label_url = f"{GITHUB_API}/repos/{REPO}/issues/{PR_NUMBER}/labels"
response = requests.post(label_url, headers=headers, json={"labels": [label]})
print(f"Label added, response status: {response.status_code}")
