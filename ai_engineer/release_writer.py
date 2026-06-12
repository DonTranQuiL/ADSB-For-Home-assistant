import os
import re
import time
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

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# Detect the project name automatically from the repo path
repo_env = os.getenv("REPO", "")
project_name = "SkyRadar Fusion"
if "grocy" in repo_env.lower():
    project_name = "Grocy"
elif repo_env:
    # E.g. "ADSB-For-Home-assistant" -> "ADSB For Home Assistant"
    project_name = repo_env.split("/")[-1].replace("-", " ").replace("_", " ").title()

# Anti-markdown-break trick
BACKTICKS = "`" * 3

prompt = f"""
You are the AI Release Manager for '{project_name}'. Your persona is Snoop Dogg.
We are dropping a brand new release, and your job is to write the official GitHub Release Notes based on the commit history.

Here are the commit titles and extended descriptions since the last release:
{changelog}

CRITICAL INSTRUCTIONS:
1. Even if there is only ONE tiny commit (e.g., "Enhance README"), you must expand it into a full, hype, professional release note.
2. Organize the markdown clearly with these categories (use them even if you have to creatively explain the small changes):
   - 🚀 What's New & Fly (The main features or updates)
   - 🛠️ Changed & Fixed (Bug fixes, tweaks)
   - ⚙️ Under the Hood (Backend, docs, chores)
3. Explain the updates in a smooth, engaging way (Snoop Dogg style, but keep it highly professional).
4. ONLY output the raw Markdown text. DO NOT wrap your response in triple backticks ({BACKTICKS}) or a code block. Just output the raw text directly.
"""

# Try calling the API with exponential backoff retries (up to 5 times)
max_retries = 5
delay = 1
completion = None

for attempt in range(max_retries):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            timeout=30.0,  # 30-second timeout
        )
        break  # Success! Break out of the retry loop.
    except Exception as e:
        if attempt == max_retries - 1:
            print(f"All {max_retries} connection attempts failed. Crash details: {e}")
            raise e
        print(f"Connection attempt {attempt + 1} failed. Retrying in {delay}s...")
        time.sleep(delay)
        delay *= 2  # Exponential backoff

try:
    release_notes = completion.choices[0].message.content.strip()

    # Clean up any accidental code block wrappers without breaking Ruff/Markdown
    pattern = rf"^{BACKTICKS}(?:markdown)?\n|\n{BACKTICKS}$"
    release_notes = re.sub(pattern, "", release_notes).strip()

    # Update GitHub Release
    repo = os.getenv("REPO")
    release_id = os.getenv("RELEASE_ID")
    token = os.getenv("GITHUB_TOKEN")

    url = f"https://api.github.com/repos/{repo}/releases/{release_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Add timeout to GitHub API call as well
    response = requests.patch(url, headers=headers, json={"body": release_notes}, timeout=15.0)

    if response.status_code == 200:
        print(f"Successfully dropped the new release notes for {project_name}!")
    else:
        print(f"Failed to update release notes. API Response: {response.text}")

except Exception as e:
    print(f"Release generation failed: {e}")
