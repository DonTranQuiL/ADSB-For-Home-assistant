import os
import re
import requests
from openai import OpenAI

# 1. Fetch the absolute latest version from PyPI
try:
    response = requests.get("https://pypi.org/pypi/FlightRadarAPI/json")
    response.raise_for_status()
    latest_version = response.json()["info"]["version"]
except Exception as e:
    print(f"Failed to fetch PyPI data: {e}")
    exit(1)

# 2. Extract current version from your requirements.txt
current_version = None
try:
    with open("requirements.txt", "r") as f:
        reqs = f.read()
        # Look for FlightRadarAPI==1.3.34 or similar
        match = re.search(r"FlightRadarAPI[=<>]+([\d\.]+)", reqs)
        if match:
            current_version = match.group(1)
except FileNotFoundError:
    print("Could not find requirements.txt")
    exit(1)

# 3. Compare versions
if not current_version or current_version == latest_version:
    print(f"FlightRadarAPI is already up to date! (Version {latest_version})")
    exit(0)

print(f"🚨 New Version Detected! Updating {current_version} -> {latest_version}")

# 4. Update the actual files
files_to_update = {
    "requirements.txt": f"FlightRadarAPI=={latest_version}",
    "requirements_test.txt": f"FlightRadarAPI=={latest_version}",
    "custom_components/skyradar_fusion/manifest.json": f"FlightRadarAPI>={latest_version}",
}

for file_path, replacement_string in files_to_update.items():
    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Replace the old version string with the new one
        new_content = re.sub(
            r"FlightRadarAPI[=<>]+[\d\.]+", replacement_string, content
        )

        with open(file_path, "w") as f:
            f.write(new_content)
        print(f"✅ Updated {file_path}")
    except FileNotFoundError:
        print(f"⚠️ Could not find {file_path}, skipping.")

# 5. Let Snoop write the PR description
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("Files updated, but no API key found for Snoop. Exiting.")
    exit(0)

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

prompt = f"""
You are the AI Staff Engineer for 'SkyRadar Fusion'. Your persona is Snoop Dogg.
You just built a bot that checks the internet for library updates, and it found one!
You automatically bumped the 'FlightRadarAPI' package from version {current_version} to {latest_version} in the manifest and requirements files.

Write a smooth, professional, yet Snoop-styled Pull Request description explaining that you updated the dependencies.
DO NOT use triple backticks or code blocks. Just output the raw text directly.
"""

try:
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    pr_body = completion.choices[0].message.content.strip()

    # Save the PR text and title for the GitHub Action to pick up
    with open("pr_body.txt", "w") as f:
        f.write(pr_body)
    with open("pr_title.txt", "w") as f:
        f.write(f"⬆️ Bump FlightRadarAPI from {current_version} to {latest_version}")

except Exception as e:
    print(f"Snoop PR generation failed: {e}")
