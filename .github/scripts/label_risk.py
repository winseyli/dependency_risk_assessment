import os
import re
import yaml
import requests

GITHUB_API = "https://api.github.com"
REPO = os.environ["GITHUB_REPOSITORY"]
PR_NUMBER = os.environ["GITHUB_REF"].split("/")[-1]
TOKEN = os.environ["GITHUB_TOKEN"]

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

# Load risk levels
with open(".github/risk-levels.yaml", "r") as f:
    risks = yaml.safe_load(f)

# Get PR title
pr_url = f"{GITHUB_API}/repos/{REPO}/pulls/{PR_NUMBER}"
pr_data = requests.get(pr_url, headers=headers).json()
title = pr_data["title"]

# Try to extract dependency name
match = re.search(r"Bump ([\w\.\-:]+) from ([\d\.]+) to ([\d\.]+)", title)
if not match:
    print("No dependency found in PR title.")
    exit(0)

dep = match.group(1)
print(f"Detected dependency: {dep}")

# Determine risk level
level = "low"
for risk_level in ["high", "medium", "low"]:
    if dep in risks.get(risk_level, []):
        level = risk_level
        break

# Apply label
label = f"risk: {level}"
print(f"Applying label: {label}")

requests.post(
    f"{pr_url}/labels",
    headers=headers,
    json={"labels": [label]},
)
