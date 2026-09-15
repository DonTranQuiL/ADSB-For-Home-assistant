"""Automated Aviation API Schema Watcher and Code Auto-Patcher for SkyRadar Fusion.

Audits live telemetry from adsb.fi and FlightRadar24. When new fields appear,
it automatically injects them into `keys_to_keep` in `coordinator.py`, verifies
syntax compilation, updates memory baselines, and drafts a PR description with Snoop Dogg.
"""

import datetime
import json
import os
import re
import requests
from FlightRadarAPI import FlightRadar24API
from openai import OpenAI

COORDINATOR_FILE = "custom_components/skyradar_fusion/coordinator.py"
MEMORY_DIR = ".memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

# Ignore internal radio feeder metrics that are not aircraft flight telemetry
IGNORE_TELEMETRY_KEYS = {
    "messages",
    "seen",
    "seen_pos",
    "rssi",
    "version",
    "sil_type",
}

# 1. Probing Configuration
FR24_API = FlightRadar24API()
ADSB_FI_BASE_URL = "https://opendata.adsb.fi/api"
ADSB_FI_LAT = 50.86
ADSB_FI_LON = 6.08
ADSB_FI_DIST_NM = 25
ADSB_FI_URL = (
    f"{ADSB_FI_BASE_URL}/v3/lat/{ADSB_FI_LAT}/lon/{ADSB_FI_LON}/dist/{ADSB_FI_DIST_NM}"
)



def get_fr24_keys():
    """Fetch live data and aggregate unique keys across visible flights."""
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

        fr24_fields = set()
        for flight in flights:
            fr24_fields.update(flight.__dict__.keys())

        return sorted(list(fr24_fields))
    except Exception as e:
        print(f"FR24 error: {e}")
        return None


def get_adsb_fi_keys():
    """Fetch live adsb.fi Open Data and aggregate unique keys across aircraft."""
    try:
        headers = {
            "User-Agent": (
                "SkyRadarFusion-Watcher/2.0 "
                "(+https://github.com/DonTranQuiL/ADSB-For-Home-assistant)"
            )
        }
        response = requests.get(ADSB_FI_URL, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        aircraft_list = data.get("ac", [])
        if not aircraft_list:
            print("adsb.fi warning: No aircraft in sample zone payload.")
            return None

        live_fields = set()
        for aircraft in aircraft_list:
            if isinstance(aircraft, dict):
                live_fields.update(aircraft.keys())

        return sorted(list(live_fields))
    except Exception as e:
        print(f"adsb.fi check failed: {e}")
        return None


sources = {"flightradar24": get_fr24_keys, "adsb_fi": get_adsb_fi_keys}
LABEL_MAP = {"flightradar24": "FR24", "adsb_fi": "adsb.fi"}

schema_drift_detected = False
auto_patched = False
report_details = []
affected_apis = []
new_telemetry_added = []

for name, fetch_func in sources.items():
    current_keys = fetch_func()
    if not current_keys:
        print(f"Skipping {name}: Environment empty or API unreachable.")
        continue

    memory_file = os.path.join(MEMORY_DIR, f"{name}_schema.json")

    try:
        with open(memory_file, "r", encoding="utf-8") as f:
            known_keys = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(current_keys, f, indent=2)
        print(f"Baseline initialized for {name}")
        continue

    added = [k for k in current_keys if k not in known_keys]

    if added:
        schema_drift_detected = True
        affected_apis.append(LABEL_MAP[name])
        report_details.append(
            f"**{LABEL_MAP[name]} Upstream Update Detected:**\nNew Fields Added: {', '.join(added)}\n"
        )

        # Update the baseline with the newly discovered fields
        updated_keys = sorted(list(set(known_keys + added)))
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(updated_keys, f, indent=2)

        if name == "adsb_fi" and os.path.exists(COORDINATOR_FILE):
            with open(COORDINATOR_FILE, "r", encoding="utf-8") as cf:
                coord_code = cf.read()

            match = re.search(
                r"keys_to_keep\s*=\s*\[(.*?)\]", coord_code, re.DOTALL
            )
            if match:
                existing_keys = re.findall(r'["\']([\w_]+)["\']', match.group(1))
                existing_set = set(existing_keys)

                fields_to_inject = [
                    k
                    for k in added
                    if k not in existing_set and k not in IGNORE_TELEMETRY_KEYS
                ]

                if fields_to_inject:
                    print(
                        f"⚡ Auto-patching coordinator.py with new fields: {fields_to_inject}"
                    )
                    combined_keys = existing_keys + fields_to_inject
                    formatted_keys = (
                        "[\n"
                        + "".join(f'            "{k}",\n' for k in combined_keys)
                        + "        ]"
                    )

                    new_coord_code = re.sub(
                        r"keys_to_keep\s*=\s*\[.*?\]",
                        f"keys_to_keep = {formatted_keys}",
                        coord_code,
                        flags=re.DOTALL,
                    )

                    # Syntax Compilation Shield
                    try:
                        compile(new_coord_code, COORDINATOR_FILE, "exec")
                        with open(COORDINATOR_FILE, "w", encoding="utf-8") as cf:
                            cf.write(new_coord_code)
                        auto_patched = True
                        new_telemetry_added.extend(fields_to_inject)
                        print("✅ coordinator.py successfully auto-patched and verified.")
                    except SyntaxError as err:
                        print(f"❌ Syntax validation failed: {err}. Skipping auto-patch.")

if schema_drift_detected:
    api_key = os.getenv("OPENROUTER_API_KEY")
    current_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    client = None
    if api_key:
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

    api_names = " & ".join(affected_apis)
    dynamic_labels = ",".join(affected_apis)

    if auto_patched and client:
        pr_prompt = f"""
You are the AI Staff Engineer for 'SkyRadar Fusion'. Your persona is Snoop Dogg.
You detected brand new live aircraft fields from {api_names}:
New Fields: {', '.join(new_telemetry_added)}

You just automatically updated `keys_to_keep` in `custom_components/skyradar_fusion/coordinator.py` and verified valid Python syntax!

Write a smooth, hype, yet professional Pull Request description explaining what fields were detected and how they improve our radar tracking data.
Keep it strictly raw Markdown text without enclosing triple backtick wrappers.
"""
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": pr_prompt}],
            )
            pr_body = completion.choices[0].message.content.strip()
        except Exception as err:
            pr_body = (
                f"Yo fam, Snoop Dogg here! Automatically injected new upstream telemetry fields "
                f"into `coordinator.py`: {', '.join(new_telemetry_added)}."
            )

        pr_title = f"✨ feat(schema): auto-track new upstream fields ({', '.join(new_telemetry_added)})"

        with open("pr_title.txt", "w", encoding="utf-8") as f:
            f.write(pr_title)
        with open("pr_body.txt", "w", encoding="utf-8") as f:
            f.write(pr_body)

    # Export variables for GitHub Actions workflow
    github_env = os.getenv("GITHUB_ENV")
    if github_env:
        with open(github_env, "a", encoding="utf-8") as f:
            f.write("SCHEMA_CHANGED=true\n")
            f.write(f"AUTO_PATCHED={'true' if auto_patched else 'false'}\n")
            f.write(
                f"ISSUE_TITLE=📡 Upstream API Alert: {api_names} Schema Changed\n"
            )
            f.write(f"API_LABELS={dynamic_labels}\n")

    print(
        f"🎉 Schema check complete. (drift={schema_drift_detected}, auto_patched={auto_patched})"
    )
else:
    print("✨ No upstream schema changes detected. Radar feeds are in sync.")
