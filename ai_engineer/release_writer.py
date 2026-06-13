import os
import re
import time
import requests

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
You are the AI Release Manager for 'YOUR REPONAME'. Your persona is Snoop Dogg.
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


def send_request_with_retry(method, url, headers, json_data, timeout, max_retries=5):
    """Performs HTTP requests with exponential backoff retries and detailed logs."""
    delay = 1
    for attempt in range(max_retries):
        try:
            print(
                f"Sending {method} request to {url} (Attempt {attempt + 1}/{max_retries})..."
            )
            if method == "POST":
                response = requests.post(
                    url, headers=headers, json=json_data, timeout=timeout
                )
            elif method == "PATCH":
                response = requests.patch(
                    url, headers=headers, json=json_data, timeout=timeout
                )
            else:
                raise ValueError(f"Unsupported method: {method}")

            # Check for success status codes
            if response.status_code in [200, 201]:
                return response
            else:
                print(
                    f"Server returned status code {response.status_code}: {response.text}"
                )
        except Exception as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")

        if attempt < max_retries - 1:
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2

    raise Exception(
        f"Failed to complete {method} request to {url} after {max_retries} attempts."
    )


try:
    # Direct requests call bypasses any OpenAI library proxy/connection pool bugs
    openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
    openrouter_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/DonTranQuiL/ADSB-For-Home-assistant",
        "X-Title": "SkyRadar Release Notes Bot",
    }
    openrouter_payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
    }

    # Connect to OpenRouter to write the release notes
    api_response = send_request_with_retry(
        method="POST",
        url=openrouter_url,
        headers=openrouter_headers,
        json_data=openrouter_payload,
        timeout=45.0,
        max_retries=5,
    )

    result = api_response.json()
    if "choices" not in result or not result["choices"]:
        raise Exception(f"Invalid API response structure: {result}")

    release_notes = result["choices"][0]["message"]["content"].strip()

    # Clean up any accidental code block wrappers without breaking Ruff/Markdown
    pattern = rf"^{BACKTICKS}(?:markdown)?\n|\n{BACKTICKS}$"
    release_notes = re.sub(pattern, "", release_notes).strip()

    # Update GitHub Release
    repo = os.getenv("REPO")
    release_id = os.getenv("RELEASE_ID")
    token = os.getenv("GITHUB_TOKEN")

    github_url = f"https://api.github.com/repos/{repo}/releases/{release_id}"
    github_headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }

    # Patch the release notes directly onto your GitHub Release page
    github_response = send_request_with_retry(
        method="PATCH",
        url=github_url,
        headers=github_headers,
        json_data={"body": release_notes},
        timeout=20.0,
        max_retries=3,
    )

    print(f"Successfully dropped the new release notes for {project_name}!")

except Exception as e:
    print(f"Release generation failed: {e}")
