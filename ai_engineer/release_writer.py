import os
import requests
from openai import OpenAI

try:
    with open("changelog.txt", "r") as f:
        changelog = f.read()
except FileNotFoundError:
    print("Could not find changelog.txt. Exiting.")
    exit(0)

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("No API key found. Exiting.")
    exit(0)

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

prompt = f"""
You are the AI Release Manager for 'SkyRadar Fusion'. Your persona is Snoop Dogg.
We are dropping a brand new release, and your job is to write the official GitHub Release Notes based on the commit history.

Here are the commit titles and extended descriptions since the last release:
{changelog}

1. Analyze these commit messages and organize them into clean, professional markdown categories:
   - 🚀 What's New (New features)
   - 🛠️ Changed & Fixed (Bug fixes, deprecated lines, updates)
   - ⚙️ Under the Hood (Backend stuff, dependency updates)
2. Explain the updates in a smooth, engaging way (Snoop Dogg style, but keep it highly professional so users understand the updates).
3. ONLY output the Markdown text for the release notes. No intro, no outro.
"""

try:
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    release_notes = completion.choices[0].message.content.strip()

    # Update GitHub Release
    repo = os.getenv("REPO")
    release_id = os.getenv("RELEASE_ID")
    token = os.getenv("GITHUB_TOKEN")

    url = f"https://api.github.com/repos/{repo}/releases/{release_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    response = requests.patch(
        url, 
        headers=headers, 
        json={"body": release_notes}
    )

    if response.status_code == 200:
        print("Successfully dropped the new release notes!")
    else:
        print(f"Failed to update release notes. API Response: {response.text}")

except Exception as e:
    print(f"Release generation failed: {e}")