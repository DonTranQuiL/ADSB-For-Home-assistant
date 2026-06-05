import os
import requests
import json
import datetime
from openai import OpenAI
from FlightRadarAPI import FlightRadar24API

# 1. Configuration
FR24_API = FlightRadar24API()
AIRPLANES_LIVE_URL = "https://api.airplanes.live/v2/point/50.86/6.08/25"
MEMORY_DIR = ".memory"
os.makedirs(MEMORY_DIR, exist_ok=True)


def get_fr24_keys():
    """Fetch live data and aggregate unique keys across ALL visible flights."""
    try:
        zones = FR24_API.get_zones()
        if not zones or "europe" not in zones:
            print("FR24 warning: Could not fetch zones.")
            return None

        bounds = FR24_API.get_bounds(zones["europe"])
        flights = FR24_API.get_flights(bounds=bounds)

        if not flights:
            print("FR24 warning: No flights in area to analyze.")
            return None

        # Loop through ALL flights to find every unique attribute available right now
        fr24_fields = set()
        for flight in flights:
            fr24_fields.update(flight.__dict__.keys())

        return sorted(list(fr24_fields))

    except Exception as e:
        print(f"FR24 error: {str(e)}")
    return None


def get_airplanes_live_keys():
    """Fetch live data and aggregate unique keys across ALL aircraft in the payload."""
    try:
        response = requests.get(AIRPLANES_LIVE_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        aircraft_list = data.get("ac", [])
        if not aircraft_list:
            print("Airplanes.live warning: No aircraft in payload zone.")
            return None

        # Loop through EVERY plane in the response and collect all unique keys
        live_fields = set()
        for aircraft in aircraft_list:
            live_fields.update(aircraft.keys())

        return sorted(list(live_fields))

    except Exception as e:
        print(f"Airplanes.live check failed: {e}")
        return None


# 2. Monitoring Logic
sources = {"flightradar24": get_fr24_keys, "airplanes_live": get_airplanes_live_keys}

schema_drift_detected = False
report_details = []

for name, fetch_func in sources.items():
    current_keys = fetch_func()
    if not current_keys:
        print(f"Skipping {name}: Environment empty or API unreachable.")
        continue

    memory_file = os.path.join(MEMORY_DIR, f"{name}_schema.json")

    # Load previous memory baseline
    try:
        with open(memory_file, "r") as f:
            known_keys = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # First-time setup: save the aggregated baseline and continue
        with open(memory_file, "w") as f:
            json.dump(current_keys, f)
        print(f"Baseline created for {name}")
        continue

    # Detect actual changes between the live aggregate and our baseline
    added = [k for k in current_keys if k not in known_keys]

    # We only trigger alerts if a completely new field is introduced by the API provider.
    if added:
        schema_drift_detected = True
        report_details.append(
            f"**{name.upper()} API Upstream Update Detected:**\nNew Fields Added: {added}\n"
        )
        # Update the baseline with the newly discovered fields
        updated_keys = sorted(list(set(known_keys + added)))
        with open(memory_file, "w") as f:
            json.dump(updated_keys, f)

# 3. Report Generation
if schema_drift_detected:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY")
    )

    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    prompt = f"""
    You are the AI Maintainer for 'SkyRadar Fusion', and your persona is Snoop Dogg. 
    You are smooth and relaxed, but you are also a highly competent, sharp technical engineer.
    
    We have a situation with the API schema:
    {chr(10).join(report_details)}
    
    You MUST format your response EXACTLY as the structured GitHub Issue template below. Fill in the technical details accurately based on the changes provided above, but write the descriptions and explanations using Snoop Dogg's slang and relaxed tone. Do not deviate from this layout.
    
    TEMPLATE:
    ### GitHub Issue Report: API Schema Changes
    **Issue Title:** [Create a technical but slightly Snoop-styled title]
    
    **Description:**
    [Write a greeting and brief explanation of the situation in Snoop's voice]
    
    **Changes:**
    **Missing Fields:**
    [List the exact missing fields as bullet points. If none, write "None"]
    
    **Added Fields:**
    [List the exact added fields as bullet points. If none, write "None"]
    
    **Potential Impact on Home Assistant Sensors:**
    * **Data Availability:** [Explain the technical impact of these specific fields using Snoop's voice]
    * **Sensor State and Attributes:** [Explain the technical impact on HA states using Snoop's voice]
    * **Integration Logic:** [Explain the technical impact on the integration code using Snoop's voice]
    
    **Next Steps:**
    [Provide an actionable bulleted list of technical steps the team needs to take to fix the issue, written in Snoop's voice]
    
    [A cool sign-off]
    
    **By:** SnoopDogg
    **Role:** AI Maintainer for SkyRadar Fusion
    **Date:** {current_date}
    """

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    with open("ai_report.md", "w") as f:
        f.write(completion.choices[0].message.content)

    with open(os.environ["GITHUB_ENV"], "a") as f:
        f.write("SCHEMA_CHANGED=true\n")
