import os
import requests
import json
from openai import OpenAI

# The endpoints your integration relies on
FEEDS = {
    "airplanes_live": "https://api.airplanes.live/v2/point/50.86/6.08/25",  # Example coordinates
    # Add your FR24 endpoint here if it has a public unauthenticated test route, or handle auth
}

schema_drift_detected = False
report_details = []

os.makedirs(".memory", exist_ok=True)

for name, url in FEEDS.items():
    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        # Extract a sample aircraft to check the schema keys
        # Adjust the path ['ac'][0] depending on the exact JSON structure
        sample_keys = list(data.get("ac", [{}])[0].keys())

        memory_file = f".memory/{name}_schema.json"

        try:
            with open(memory_file, "r") as f:
                known_schema = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            with open(memory_file, "w") as f:
                json.dump(sample_keys, f)
            continue

        added = [k for k in sample_keys if k not in known_schema]
        missing = [k for k in known_schema if k not in sample_keys]

        if added or missing:
            schema_drift_detected = True
            report_details.append(
                f"**{name.upper()} API Changes:**\nMissing: {missing}\nAdded: {added}\n"
            )

            # Update memory to the new broken/changed schema so it doesn't alert twice
            with open(memory_file, "w") as f:
                json.dump(sample_keys, f)

    except Exception as e:
        print(f"Failed to check {name}: {e}")

if not schema_drift_detected:
    print("Both aviation APIs are stable.")
    exit(0)

# If we get here, an API broke. Let's write the report.
client = OpenAI(
    base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY")
)

prompt = f"""
You are the AI maintainer for SkyRadar Fusion, a Home Assistant ADSB integration.
One of our upstream flight data APIs just changed its schema.

Changes detected:
{chr(10).join(report_details)}

Write a highly technical GitHub Issue report for the maintainer. 
1. Note the specific fields that changed.
2. Warn about which Home Assistant sensors might break (e.g., altitude, heading, speed).
3. Suggest the Python fix required in the data coordinator.
"""

completion = client.chat.completions.create(
    model="meta-llama/llama-3-8b-instruct:free",
    messages=[{"role": "user", "content": prompt}],
)

with open("ai_report.md", "w") as f:
    f.write(completion.choices[0].message.content)

with open(os.environ["GITHUB_ENV"], "a") as f:
    f.write("SCHEMA_CHANGED=true\n")
