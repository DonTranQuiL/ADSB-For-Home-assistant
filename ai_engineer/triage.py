import os
import requests
from openai import OpenAI

issue_title = os.getenv("ISSUE_TITLE", "")
issue_body = os.getenv("ISSUE_BODY", "")
issue_number = os.getenv("ISSUE_NUMBER")
repo = os.getenv("GITHUB_REPOSITORY")
token = os.getenv("GITHUB_TOKEN")

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    exit(0)

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

prompt = f"""
You are the AI maintainer for "SkyRadar Fusion", a Home Assistant ADSB integration.
A user opened an issue. 

Title: {issue_title}
Body: {issue_body}

Analyze it and reply strictly in this plain text format:
LABELS: <comma separated labels from: bug, enhancement, needs-info>
COMMENT: <your polite response>

Rules for the comment:
- If it's a feature request for new aircraft data points (like squawk codes, vertical speed), label as 'enhancement' and politely explain that new data points must be evaluated against FlightRadar24 API limits.
- If it's a bug but missing Home Assistant logs, label as 'bug, needs-info' and ask for logs.
"""

try:
    completion = client.chat.completions.create(
        model="meta-llama/llama-3-8b-instruct:free",
        messages=[{"role": "user", "content": prompt}],
    )

    lines = completion.choices[0].message.content.strip().splitlines()
    labels = []
    comment = ""

    for line in lines:
        if line.startswith("LABELS:"):
            labels_str = line.replace("LABELS:", "").strip()
            labels = [label.strip() for label in labels_str.split(",") if label.strip()]
        elif line.startswith("COMMENT:"):
            comment = line.replace("COMMENT:", "").strip()

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    if labels:
        requests.post(
            f"https://api.github.com/repos/{repo}/issues/{issue_number}/labels",
            headers=headers,
            json={"labels": labels},
        )
    if comment:
        requests.post(
            f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments",
            headers=headers,
            json={"body": f"?? **AI Triage:**\n\n{comment}"},
        )

except Exception as e:
    print(f"Failed triage: {e}")
