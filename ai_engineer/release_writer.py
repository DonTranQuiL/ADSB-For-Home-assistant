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
    project_name = repo_env.split("/")[-1].replace("-", " ").replace("_", " ").title()

# Extract metadata
tag_name = os.getenv("RELEASE_TAG", "v1.0.0")
release_title = os.getenv("RELEASE_NAME", "")

BACKTICKS = "`" * 3

prompt = f"""
You are the Lead Release Engineer and technical storyteller for {project_name}.
Write the official GitHub Release Notes for version {tag_name} using the commit history and code diffs below.

Commit Log & Diffs:
{changelog}

STRICT OUTPUT FORMAT RULES:
1. Title Header:
   Generate an energetic, thematic header in this exact format:
   ## 🚀 {project_name} {tag_name} - <Punchy Theme Name> <Matching Emojis>
   (Example: "## 🚀 SkyRadar Fusion v2.0.11 - Unstoppable Radar Edition ✈️📡")

2. Hook Paragraph:
   Write a bold 2-3 sentence executive summary explaining the core value of this update, addressing stability, performance, or major architectural leaps directly.

3. Main Sections (use these exact H2/H3 markers):
   ### 🚀 What's New & Fly
   - Group major user-facing additions or integrations.
   - Format each entry with bold topic tags: "**Feature Name:** Clear, energetic explanation of what it improves."

   ## 🛠️ Changed & Fixed
   - Format items as "**Target Area/Fix:** Concrete explanation of what broke, what changed, and the result."

   ## ⚙️ Under the Hood
   - Document refactors, lint sweeps (Ruff), typing, telemetry guards, or dependencies.

4. Sign-off Line:
   End with a warm community closing sentence and thematic emojis (e.g., "Thank you to the community and everyone running an open feeder to keep the skies transparent! ✈️🌍").

TONE AND CONTENT GUIDELINES:
- Professional, technical, yet highly enthusiastic and confident.
- Do not make generic bullet points. Detail the actual modules changed (e.g., mention file targets like api.py, coordinator.py, or explicit endpoints if visible in the diff).
- DO NOT wrap the output in triple backticks or markdown fences. Output raw markdown only.
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
    openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
    openrouter_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": f"https://github.com/{repo_env}",
        "X-Title": f"{project_name} Release Notes Bot",
    }
    openrouter_payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
    }

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

    # Strip accidental wrapping markdown code fences (```markdown ... ```)
    release_notes = re.sub(r"^```(?:markdown)?\s*\n", "", release_notes)
    release_notes = re.sub(r"\n```\s*$", "", release_notes).strip()

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
