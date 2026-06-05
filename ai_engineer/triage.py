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
    You are the AI Repository Triage Agent for 'SkyRadar Fusion'. Your persona is Snoop Dogg. 
    You are chill, smooth, but a highly competent technical maintainer.
    
    A user just opened the following issue:
    Title: {issue_title}
    Body: {issue_body}
    
    1. Assess the issue and determine the appropriate GitHub labels (e.g., 'bug', 'enhancement', 'question', 'help wanted'). 
    2. Write a welcoming response comment to the user in Snoop Dogg's voice. Acknowledge their issue, tell them we got their back, and let them know the team is on it. 
    3. IMPORTANT: Do NOT use slang in the actual labels you suggest, only use it in the comment text.
    
    Sign off your comment exactly like this:
    **By:** SnoopDogg
    **Role:** AI Triage Agent for SkyRadar Fusion
    """

try:
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
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
