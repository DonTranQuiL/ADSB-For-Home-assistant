import os
import requests
import json
from openai import OpenAI
from FlightRadarAPI import FlightRadar24API

# 1. Configuration
FR24_API = FlightRadar24API()
AIRPLANES_LIVE_URL = "https://api.airplanes.live/v2/point/50.86/6.08/25"
MEMORY_DIR = ".memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

schema_drift_detected = False
report_details = []


def get_fr24_keys():
    """Fetch sample keys using the library properly."""
    try:
        # 1. Warm up the API by fetching zones
        zones = FR24_API.get_zones()
        if not zones:
            print("FR24 warning: Could not fetch zones.")
            return None

        # 2. Use a specific zone instead of arbitrary bounds
        # 'europe' is usually well-populated
        flights = FR24_API.get_flights(zone=zones["europe"])

        if flights:
            return list(flights[0].__dict__.keys())

    except Exception as e:
        print(f"FR24 error: {str(e)}")
    return None


def get_airplanes_live_keys():
    """Fetch sample keys using the REST API."""
    try:
        response = requests.get(AIRPLANES_LIVE_URL, timeout=10)
        data = response.json()
        sample_data = data.get("ac", [{}])[0]
        return list(sample_data.keys())
    except Exception as e:
        print(f"Airplanes.live check failed: {e}")
    return None


# 2. Monitor Loop
sources = {"flightradar24": get_fr24_keys, "airplanes_live": get_airplanes_live_keys}

for name, fetch_func in sources.items():
    current_keys = fetch_func()
    if not current_keys:
        print(f"Could not fetch data for {name}, skipping.")
        continue

    memory_file = os.path.join(MEMORY_DIR, f"{name}_schema.json")

    # Load previous memory
    try:
        with open(memory_file, "r") as f:
            known_keys = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # First run: Save and skip
        with open(memory_file, "w") as f:
            json.dump(current_keys, f)
        print(f"Baseline created for {name}")
        continue

    # Detect Drift
    added = [k for k in current_keys if k not in known_keys]
    missing = [k for k in known_keys if k not in current_keys]

    if added or missing:
        schema_drift_detected = True
        report_details.append(
            f"**{name.upper()} API Changes:**\nMissing: {missing}\nAdded: {added}\n"
        )

        # Update memory
        with open(memory_file, "w") as f:
            json.dump(current_keys, f)

# 3. Report if needed
if schema_drift_detected:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY")
    )

    prompt = f"""
    You are the AI maintainer for SkyRadar Fusion. One of our flight data APIs changed its schema.
    Changes:
    {chr(10).join(report_details)}
    
    Write a technical GitHub Issue report. Identify the changes and potential impact on Home Assistant sensors.
    """

    completion = client.chat.completions.create(
        model="meta-llama/llama-3-8b-instruct:free",
        messages=[{"role": "user", "content": prompt}],
    )

    with open("ai_report.md", "w") as f:
        f.write(completion.choices[0].message.content)

    with open(os.environ["GITHUB_ENV"], "a") as f:
        f.write("SCHEMA_CHANGED=true\n")
