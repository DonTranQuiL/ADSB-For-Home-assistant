import os
import requests
from openai import OpenAI

try:
    with open("pr_diff.txt", "r") as f:
        diff_text = f.read()
except FileNotFoundError:
    print("No diff found, exiting.")
    exit(0)

if len(diff_text.strip()) < 10:
    print("Empty diff, skipping review.")
    exit(0)

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("No API key found. Skipping AI review.")
    exit(0)

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

prompt = f"""
You are the AI Senior Code Reviewer for 'SkyRadar Fusion'. Your persona is Snoop Dogg.
You are the gatekeeper keeping the codebase fresh, clean, and tight.

Here is the Pull Request diff:
{diff_text}

1. Review the code for bugs, efficiency, architecture, and cleanliness.
2. Write your review summary in Snoop Dogg's voice. If it's fly, give it some praise. If it needs work or has security holes, point out the flaws smoothly and tell the dev how to fix it.
3. Any code snippets you suggest must be strictly professional standard Python.

Sign off your review exactly like this:
**By:** SnoopDogg
**Role:** AI Code Reviewer for SkyRadar Fusion
"""

completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
)

review_comment = completion.choices[0].message.content.strip()

if review_comment != "APPROVED":
    print("Issues found. Posting comment...")
    repo = os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("PR_NUMBER")
    token = os.getenv("GITHUB_TOKEN")

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    requests.post(
        url,
        headers=headers,
        json={"body": f"🔍 **AI Architecture Review:**\n\n{review_comment}"},
    )
else:
    print("Code looks good! No comment needed.")
