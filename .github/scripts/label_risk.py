import os
import re
import yaml
import json
import requests

GITHUB_API = "https://api.github.com"
REPO = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ["GITHUB_TOKEN"]

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

# Load event payload to get PR number
event_path = os.environ["GITHUB_EVENT_PATH"]
with open(event_path, 'r') as f:
    event_data = json.load(f)
pr_number = event_data["number"]

# Load risk levels
with open(".github/risk-levels.yaml", "r") as f:
    risks = yaml.safe_load(f)

# Get PR title
pr_url = f"{GITHUB_API}/repos/{REPO}/pulls/{pr_number}"
pr_data = requests.get(pr_url, headers=headers).json()

if "title" not in pr_data:
    print(f"Cannot find title in PR response: {pr_data}")
    exit(1)

title = pr_data["title"]
print(f"Detected PR title: {title}")

# Parse dependency
match = re.search(r"Bump ([\w\.\-:]+) from ([\d\.]+) to ([\d\.]+)", title)
if not match:
    print("No dependency pattern matched in PR title.")
    exit(0)

dep = match.group(1)

# Risk level detection
level = "low"
for risk_level in ["high", "medium", "low"]:
    if dep in risks.get(risk_level, []):
        level = risk_level
        break

# Apply label
label = f"risk: {level}"
print(f"Applying label: {label}")

label_url = f"{GITHUB_API}/repos/{REPO}/issues/{pr_number}/labels"
response = requests.post(label_url, headers=headers, json={"labels": [label]})
print(f"Label added, response status: {response.status_code}")
