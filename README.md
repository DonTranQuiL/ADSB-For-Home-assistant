<div align="center">

# 📡 SkyRadar Fusion
**The high-performance, zero-bloat, hybrid ADS-B & FlightRadar24 airspace intelligence monitor for Home Assistant.**

> ⚠️ **MASSIVE OVERHAUL ANNOUNCEMENT:** > We have just released a gigantic core rewrite! This integration (formerly Airplanes.Live Tracker) now features a **Hybrid Engine**, combining the ultra-fast Airplanes.Live radar feed with rich **FlightRadar24 API enrichment** (live routes, high-res photos, and scheduled times). Welcome to the SkyRadar Fusion era!

[![Latest Release](https://img.shields.io/github/v/release/DonTranQuiL/ADSB-For-Home-assistant?style=for-the-badge&color=007ec6)](https://github.com/DonTranQuiL/ADSB-For-Home-assistant/releases)
[![License](https://img.shields.io/github/license/DonTranQuiL/ADSB-For-Home-assistant?style=for-the-badge&color=007ec6)](https://github.com/DonTranQuiL/ADSB-For-Home-assistant/blob/main/LICENSE)
[![Home Assistant CI](https://img.shields.io/github/actions/workflow/status/DonTranQuiL/ADSB-For-Home-assistant/hass-ci.yml?label=Home%20Assistant%20CI&style=for-the-badge)](https://github.com/DonTranQuiL/ADSB-For-Home-assistant/actions/workflows/hass-ci.yml)
[![Code Checks](https://img.shields.io/github/actions/workflow/status/DonTranQuiL/ADSB-For-Home-assistant/codechecker.yml?style=for-the-badge&label=CODE%20CHECKS&color=5dbb0f)](https://github.com/DonTranQuiL/ADSB-For-Home-assistant/actions)
[![Tests](https://img.shields.io/github/actions/workflow/status/DonTranQuiL/ADSB-For-Home-assistant/pytest.yml?style=for-the-badge&label=TESTS&color=5dbb0f)](https://github.com/DonTranQuiL/ADSB-For-Home-assistant/actions)
[![HACS Validation](https://img.shields.io/github/actions/workflow/status/DonTranQuiL/ADSB-For-Home-assistant/hacs.yaml?style=for-the-badge&label=HACS%20VALIDATION&color=5dbb0f)](https://github.com/DonTranQuiL/ADSB-For-Home-assistant/actions)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-5dbb0f?style=for-the-badge)](https://github.com/pre-commit/pre-commit)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000?style=for-the-badge)](https://github.com/astral-sh/ruff)
[![HACS Custom](https://img.shields.io/badge/HACS-CUSTOM-ff6e27?style=for-the-badge)](https://hacs.xyz/)
[![Home Assistant Version](https://img.shields.io/badge/Home%20Assistant-2025.1%2B-007ec6?style=for-the-badge)](https://www.home-assistant.io/)
[![Maintainer](https://img.shields.io/badge/maintainer-%40DonTranQuiL-007ec6?style=for-the-badge)](https://github.com/DonTranQuiL)
[![Donate](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-ffdd00?style=for-the-badge)](https://ko-fi.com/DonTranQuiL)
[![Community Forum](https://img.shields.io/badge/community-forum-007ec6?style=for-the-badge)](https://community.home-assistant.io/t/ads-b-tracker-for-home-assistant/1011081)

</div>

### 🚀 High-Performance Airspace Intelligence
Bring ultra-fast, live aviation telemetric streams directly into Home Assistant using open-access ADS-B feeds, now heavily enriched with FlightRadar24 data. Engineered with a strict optimization-first mindset, this component consolidates all regional lookups into **one single aggregated network request per polling cycle**. Say goodbye to Cloudflare blocks, aggressive API rate bans, and home automation host slowdowns.

---

## 📥 How to Install (via HACS)

The most efficient deployment method is through **HACS** (Home Assistant Community Store):

1. Open **HACS** in your sidebar and navigate into the **Integrations** panel.
2. Click the three dots (`...`) located in the upper right quadrant and select **Custom repositories**.
3. Input the repository web link: `https://github.com/DonTranQuiL/ADSB-For-Home-assistant`
4. Set the Category selector dropdown to **Integration** and hit **Add**.
5. Locate the newly added **SkyRadar Fusion** repository card and hit **Download**.
6. ⚠️ **Restart your Home Assistant instance**.
7. Navigate to **Settings > Devices & Services > Add Integration**, lookup **SkyRadar Fusion**, and configure your primary boundary coordinates.

---

## ✈️ How to Enable FlightRadar24 Enrichment
Because the FR24 Enrichment makes additional API calls on your behalf, it is strictly **Opt-In**. Here is how to turn on the magic:

1. Go to **Settings > Devices & Services** in Home Assistant.
2. Find the **SkyRadar Fusion** integration card.
3. Click on **Configure**.
4. Check the box that says **"Enable FlightRadar24 Enrichment (Photos & Routes)"**.
5. Click **Submit**. 
*(Boom! Your map trackers will now instantly populate with high-res photos and live route data).*

---

## 🌟 Massive New Features & Architecture

### 🌍 FlightRadar24 Enrichment API (The Hybrid Engine)
We have merged the raw speed of local ADS-B feeds with the rich data of FlightRadar24! Your tracked entities on the map now automatically populate with:
* **High-Res Aircraft Photos:** Automatically fetched and applied as the entity picture.
* **Live Route Data:** See the Origin and Destination airports (e.g., `CDG - AMS`).
* **Airline Identification:** Know exactly which carrier operates the flight.
* **Timetables:** View Scheduled Departure, Actual Departure, and Estimated Time of Arrival (ETA) directly in the tracker attributes.

### 👻 Offline "Ghost" Tracking
Want to track a flight before it even takes off? The integration supports "Ghost Tracking." If you enter a flight number that is currently out of radar range (e.g., sitting at the gate), the system generates an offline dummy entity. FlightRadar24 then steps in to inject the scheduled departure times, routes, and photos *before* the plane is airborne!

### 🧊 Intelligent Timeout "Freezer" Logic
No more flashing or disappearing entities on your dashboard! If the upstream APIs experience a temporary delay or heavy server load, the integration recognizes the network glitch and instantly "freezes" your data on the last known good state, maintaining perfect UI stability until a fresh payload arrives.

### 📍 Dynamic Options Flow
Change your radar's center point on the fly! You can now adjust your tracking Latitude, Longitude, and Radius directly from the integration's `Options` menu without having to delete and reinstall the component.

---

## Tracking feature and live feed on your maps, with the image of the plane!

### 1️⃣ Add a Callsign to Track
Enter any live callsign into the tracking field and it will instantly appear inside your additional tracked targets.

<p align="center">
  <img src="https://github.com/user-attachments/assets/7c493baa-f350-4b65-be2b-1624100b0cff"
       width="320"
       alt="Add callsign to tracking list">
</p>

### 2️⃣ Add the Aircraft Entity to Your Map
Tracked aircraft entities always follow this format:

```text
device_tracker.airplanes_live_CALLSIGN
```

Add the entity directly into a Lovelace Map card. The tracked entities are not visible in the integration as a separate sensor, keeping your system perfectly organized! 

<p align="center">
  <img src="https://github.com/user-attachments/assets/ac3420f7-4a3e-4f36-89da-41e08cb9265e"
       width="300"
       alt="Map entity example">
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/0a723c32-a90e-4ed2-8d8d-53ecb442d883"
       width="500"
       alt="Tracked aircraft on map">
</p>

---

### 🧹 Real-Time Zero-Bloat Entity Cleanup
Standard aviation integrations spin up permanent entities for every flying hull, corrupting the Home Assistant Entity Registry and Recorder database with hundreds of dead historical links or crashing it by exceeding the 16KB attribute limit. This component enforces a strict **Zero-Bloat Gatekeeping Policy**:
* The global counters (`sensor.global_emergencies` & `sensor.global_military`) are hyper-optimized to only store a lightweight, readable list of active flights in their attributes. Detailed data is offloaded safely to the map trackers.
* Individual `device_tracker` entities are generated **only** for targets explicitly locked on your watchlist or detected globally.
* The moment a flight lands or leaves your parameters, the integration dynamically hooks into the Home Assistant Core `entity_registry` and applies an aggressive `force_remove` command. No lingering `Unknown` or `Unavailable` states, and a pristine database.

### 💾 Safe State Restoration across Reboots
Because the tracking lists are stored dynamically in memory to ensure UI speed, the integration features a specialized **`RestoreSensor` (`sensor.additional_tracked`)**. This module acts as an encrypted state bucket. On server reboots or system crashes, it parses historical database records, reads the active tracking arrays, and instantly rebuilds your watchlist on startup.

---

## ✨ Core Platforms & Sensors

### 📊 Local Airspace Telemetry
When configured in **Zone Tracking Mode**, the integration maps local coordinates against the API feed using native metric haversine math to break down immediate regional traffic:
* `sensor.current_in_area`: Total count of active airframes currently inside your metric barrier.
* `sensor.entered_area`: Real-time sweep counter indicating how many airframes passed *into* your operational boundary on the last tick.
* `sensor.exited_area`: Sweep counter identifying airframes leaving your metric airspace footprint.
* `sensor.[Category]_s_in_area`: Dynamic classification trackers splitting local airspace counts on-the-fly into dedicated subset entities (`Helicopters`, `Military`, `Commercial`, `Private`).

### 🌍 Global Strategic Radars (Configurable Toggles)
Tap into worldwide events directly through the integration options menu:
* **Global Emergency Radar (Squawk 7700):** Continually monitors the entire planet for active transponders broadcasting an emergency, computing the real-time distance relative to your home coordinates. Generates instant map trackers for affected flights!
* **Global Military Radar:** Monitors active tactical airframes across the globe, listing absolute frame data and generating live map trackers for all military assets.
* *Note: The radius configuration is in meters (e.g., 5000 = 5km).*

### 🛠️ Core Diagnostic Suite
Tucked away safely inside the native Home Assistant `Diagnostic` entity category, you can monitor tracking pipeline integrity in real-time:
* `sensor.airplanes_live_consecutive_errors`: Integer counter displaying consecutive API network timeout or fetch failures.
* `sensor.airplanes_live_last_update_status`: State string exposing the explicit health status of the network endpoint loop (`Success`, `Pending`, `Failed`).
* `sensor.airplanes_live_last_update_time`: Precise ISO Timestamp showing the last successful data retrieval.

---

## 🏎️ Adaptive Telemetry & ICAO Fallback Icons
Missing a profile picture on FR24 or Planespotters? Target tracking entities automatically bind to a highly reactive Material Design Icon suite that alters visual representation based on immediate telemetric parameters and vertical climb speeds (`baro_rate`):
* 🛫 **Climbing (`baro_rate > 250 ft/min`):** Transforms to `mdi:airplane-takeoff`
* 🛬 **Descending (`baro_rate < -250 ft/min`):** Transforms to `mdi:airplane-landing`
* 🚁 **Rotorcraft / Helicopters:** Hard-locked onto `mdi:helicopter` for clean visual scanning.
* 🎈 **Balloons / Gliders:** Dynamically swaps indicators to specialized icons (`mdi:hot-air-balloon` or `mdi:paper-airplane`).
* 🚫 **Offline Ghost Tracker:** Shows `mdi:airplane-off` when waiting for FR24 data before departure.

---

## 🗺️ Local Liveries Asset Mapping (Custom Fallback)
If the external photo APIs draw a blank for specific experimental hulls or secure assets, the system falls back onto your local file server structure using an advanced asynchronous non-blocking frontend asset path (`/airplanes_live_assets/`).
1. Navigate inside your core file system to `/config/custom_components/airplanes_live/`
2. Create a folder hierarchy named `www/planes/`
3. Drop transparent `.png` files inside that folder, matching the official uppercase ICAO type signature (e.g., `/planes/B77W.png` or `/planes/A320.png`).
4. The tracking maps will cleanly prioritize these assets before resorting to default MDI icon mappings.

---

## ⚙️ Interactive Lovelace Dashboard Configurations
Take advantage of the integrated `text` and `button` controllers to build complete airfield operational panels directly inside your standard Lovelace grid setups:

### Lovelace Card Control Example
```yaml
type: entities
title: "Airspace Watchlist Controls"
show_header_toggle: false
entities:
  - entity: text.airplanes_live_tracker_add_to_track
    name: "🚀 Target Flight Lock"
  - entity: text.airplanes_live_tracker_remove_from_track
    name: "🗑️ Release Flight Lock"
  - entity: button.airplanes_live_tracker_clear_additional_tracked
    name: "🧹 Wipe Target Registry"
```
