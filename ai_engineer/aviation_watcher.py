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

def get_fr24_keys():
    """Fetch sample keys using the library correctly."""
    try:
        # Fetch zones and convert 'europe' to bounds
        zones = FR24_API.get_zones()
        if not zones or 'europe' not in zones:
            print("FR24 warning: Could not fetch zones.")
            return None
            
        # Use get_bounds to convert the zone to the correct format for get_flights
        bounds = FR24_API.get_bounds(zones['europe'])
        flights = FR24_API.get_flights(bounds=bounds)
        
        if flights:
            # Flight object attributes are stored in __dict__
            return list(flights[0].__dict__.keys())
            
    except Exception as e:
        print(f"FR24 error: {str(e)}")
    return None

def get_airplanes_live_keys():
    """Fetch sample keys using the REST API."""
    try:
        response = requests.get(AIRPLANES_LIVE_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Look for aircraft list 'ac'
        sample_data = data.get("ac", [{}])[0]
        return list(sample_data.keys())
    except Exception as e:
        print(f"Airplanes.live check failed: {e}")
    return None

# 2. Monitoring Logic
sources = {
    "flightradar24": get_fr24_keys,
    "airplanes_live": get_airplanes_live_keys
}

schema_drift_detected = False
report_details = []

for name, fetch_func in sources.items():
    current_keys = fetch_func()
    if not current_keys:
        print(f"Skipping {name}: No data returned.")
        continue
    
    memory_file = os.path.join(MEMORY_DIR, f"{name}_schema.json")
    
    # Load previous memory
    try:
        with open(memory_file, "r") as f:
            known_keys = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Baseline creation
        with open(memory_file, "w") as f:
            json.dump(current_keys, f)
        print(f"Baseline created for {name}")
        continue
        
    # Detect Drift
    added = [k for k in current_keys if k not in known_keys]
    missing = [k for k in known_keys if k not in current_keys]
    
    if added or missing:
        schema_drift_detected = True
        report_details.append(f"**{name.upper()} API Changes:**\nMissing: {missing}\nAdded: {added}\n")
        with open(memory_file, "w") as f:
            json.dump(current_keys, f)

# 3. Report Generation
if schema_drift_detected:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1", 
        api_key=os.getenv("OPENROUTER_API_KEY")
    )
    
    prompt = f"""
    You are the AI maintainer for SkyRadar Fusion. One of our flight data APIs changed its schema.
    Changes:
    {chr(10).join(report_details)}
    
    Write a technical GitHub Issue report. Identify the changes and potential impact on Home Assistant sensors.
    """
    
    completion = client.chat.completions.create(
        model="google/gemini-2.0-flash-lite-preview-02-05:free",
        messages=[{"role": "user", "content": prompt}]
    )
    
    with open("ai_report.md", "w") as f:
        f.write(completion.choices[0].message.content)
        
    # Signal GitHub Actions that a change was detected
    with open(os.environ['GITHUB_ENV'], 'a') as f:
        f.write("SCHEMA_CHANGED=true\n")
