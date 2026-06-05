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
You are an expert Home Assistant Core maintainer reviewing a pull request for the 'SkyRadar Fusion' ADSB integration.
Review the following code diff. 

Look specifically for these critical Home Assistant mistakes:
1. `api.py` or `coordinator.py`: The `FlightRadar24API` is fully synchronous. Ensure NO calls to it are made directly in async functions. They MUST be wrapped in `await self.hass.async_add_executor_job`.
2. `sensor.py`: Ensure any new entity using `CoordinatorEntity` properly defines `_attr_unique_id`.
3. General: Ensure dictionary parsing uses `.get("key")` instead of direct `["key"]` access, as ADS-B data is highly prone to missing fields.

If the code looks perfect, respond ONLY with the word "APPROVED".
If there are issues, write a short, polite GitHub PR comment highlighting the specific files and line numbers, and suggest the fix. Do not use JSON formatting.

Diff:
{diff_text}
"""

completion = client.chat.completions.create(
    model="meta-llama/llama-3-8b-instruct:free",
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
        json={"body": f"?? **AI Architecture Review:**\n\n{review_comment}"},
    )
else:
    print("Code looks good! No comment needed.")
