<div align="center">

<img width="870" height="421" alt="{A495DBAA-24A4-4C04-9EAA-7D8B39A8541F}" src="https://github.com/user-attachments/assets/29b30b18-df46-420c-b2eb-e0227417b0dd" />



# 📡 SkyRadar Fusion
**The high-performance, zero-bloat, hybrid ADS-B & FlightRadar24 airspace intelligence monitor for Home Assistant.**

> ⚠️ **MASSIVE OVERHAUL ANNOUNCEMENT:** 
> We have just released a gigantic core rewrite! This integration (formerly Airplanes.Live Tracker) now features a **Hybrid Engine**, combining the ultra-fast Airplanes.Live radar feed with rich **FlightRadar24 API enrichment** (live routes, high-res photos, and scheduled times). Welcome to the SkyRadar Fusion era!

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

## ✈️ The Hybrid Engine: FlightRadar24 Enrichment
Because the FR24 Enrichment makes additional API calls on your behalf, it is highly customizable to protect your IP from rate limits. When enabled, your explicitly tracked targets and overhead flights will populate with **Flight Intelligence Data**:
* **High-Res Aircraft Photos:** Automatically fetched and applied as the entity picture.
* **Live Route Data:** View exact Origin and Destination cities & countries (e.g., `Paris, FR -> Amsterdam, NL`).
* **Airline Identification:** Know exactly which carrier operates the flight.
* **Timetables:** View Scheduled Arrival and live Estimated Time of Arrival (ETA).

### ☁️ The "Overhead Bubble"
You can define a secondary, tighter radius (e.g., 3000 meters) known as the **FR24 Overhead Bubble**. Any aircraft flying directly over your house within this bubble will automatically fetch the rich FR24 data and photos for your dashboard sensors, **without** creating map trackers! This keeps your map clean and your API calls incredibly low.

### 🎛️ Surgical API Control (Category Filters)
To prevent your integration from wasting API calls on local hobby pilots or trauma helicopters, you have full control over the Overhead Bubble:
* ✅ **Enrich Commercial Flights** (Airliners)
* ✅ **Enrich Private Aircraft** (Cessnas, Business Jets)
* ✅ **Enrich Helicopters**

### 🔓 Advanced Power User Mode
If you are a hardcore aviation enthusiast, you can bypass the standard checkboxes. Enter specific ADS-B Emitter Categories (e.g., `A3, A5`) into the **Advanced ADS-B Filter** text box in the options menu. The integration will strictly fetch FR24 data *only* for aircraft matching those exact raw ADS-B codes!

---

## 🌟 Core Features & Architecture

### 👻 Offline "Ghost" Tracking
Want to track a flight before it even takes off? The integration supports "Ghost Tracking." If you enter a flight number that is currently out of radar range (e.g., sitting at the gate), the system generates an offline dummy entity. FlightRadar24 then steps in to inject the scheduled departure times, routes, and photos *before* the plane is airborne!

### 🧊 Intelligent Timeout "Freezer" Logic
No more flashing or disappearing entities on your dashboard! If the upstream APIs experience a temporary delay or heavy server load, the integration recognizes the network glitch and instantly "freezes" your data on the last known good state, maintaining perfect UI stability until a fresh payload arrives.

### 🧹 Real-Time Zero-Bloat Entity Cleanup
Standard aviation integrations spin up permanent entities for every flying hull, corrupting the Home Assistant database. This component enforces a strict **Zero-Bloat Gatekeeping Policy**:
* Global counters (`sensor.global_emergencies`) only store lightweight data.
* `device_tracker` entities are **only** generated for explicitly tracked targets, military, or emergencies.
* Once a flight leaves your parameters, the integration dynamically hooks into the HA Core and applies an aggressive `force_remove`. No lingering `Unknown` states, maintaining a pristine database.

### 💾 Safe State Restoration across Reboots
Tracking lists are stored dynamically in memory for maximum speed. On server reboots or system crashes, the specialized **`RestoreSensor` (`sensor.additional_tracked`)** reads the encrypted historical database arrays and instantly rebuilds your watchlist on startup.

---

## 📍 Tracking features and live maps

### 1️⃣ Add a Callsign to Track
Enter any live callsign into the tracking field and it will instantly appear inside your additional tracked targets. *(This instantly triggers a full FR24 data pull for this specific flight!)*

<p align="center">
  <img src="https://github.com/user-attachments/assets/7c493baa-f350-4b65-be2b-1624100b0cff"
       width="320"
       alt="Add callsign to tracking list">
</p>

### 2️⃣ Add the Aircraft Entity to Your Map
Tracked aircraft entities always follow this format:

```text
device_tracker.skyradar_fusion_CALLSIGN
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

## ✨ Core Platforms & Sensors

### 📊 Local Airspace Telemetry (Zone Tracking)
* `sensor.current_in_area`: Total count of active airframes currently inside your primary metric barrier.
* `sensor.entered_area`: Sweep counter indicating how many airframes passed *into* your operational boundary on the last tick.
* `sensor.exited_area`: Sweep counter identifying airframes leaving your metric airspace footprint.
* `sensor.[Category]_s_in_area`: Dynamic classification trackers splitting local airspace counts on-the-fly (`Helicopters`, `Military`, `Commercial`, `Private`).

### 🌍 Global Strategic Radars
* **Global Emergency Radar (Squawk 7700):** Continually monitors the entire planet for active transponders broadcasting an emergency. Generates instant map trackers for affected flights!
* **Global Military Radar:** Monitors active tactical airframes across the globe, listing absolute frame data and generating live map trackers for all military assets.

### 🛠️ Core Diagnostic Suite
Tucked away safely inside the native Home Assistant `Diagnostic` entity category:
* `sensor.skyradar_fusion_consecutive_errors`: Exposes API network timeout or fetch failures.
* `sensor.skyradar_fusion_last_update_status`: Health status of the network loop (`Success`, `Pending`, `Failed`).

---

## 🏎️ Adaptive Telemetry & ICAO Fallback Icons
Target tracking entities automatically bind to a highly reactive Material Design Icon suite that alters visual representation based on vertical climb speeds (`baro_rate`):
* 🛫 **Climbing (`baro_rate > 250 ft/min`):** Transforms to `mdi:airplane-takeoff`
* 🛬 **Descending (`baro_rate < -250 ft/min`):** Transforms to `mdi:airplane-landing`
* 🚁 **Rotorcraft / Helicopters:** Hard-locked onto `mdi:helicopter`.
* 🚫 **Offline Ghost Tracker:** Shows `mdi:airplane-off` when waiting for departure.

---

## 🗺️ Local Liveries Asset Mapping (Custom Fallback)
If the external photo APIs draw a blank, the system falls back onto your local file server structure:
1. Navigate inside your core file system to `/config/custom_components/skyradar_fusion/`
2. Create a folder hierarchy named `www/planes/`
3. Drop transparent `.png` files inside that folder, matching the official uppercase ICAO type signature (e.g., `/planes/B77W.png`).
4. The tracking maps will cleanly prioritize these assets before resorting to MDI icons.

---

## ⚙️ Interactive Lovelace Dashboard Configurations
Build complete airfield operational panels directly inside your Lovelace grid setups:

### Lovelace Card Control Example
```yaml
type: entities
title: "Airspace Watchlist Controls"
show_header_toggle: false
entities:
  - entity: text.skyradar_fusion_tracker_add_to_track
    name: "🚀 Target Flight Lock"
  - entity: text.skyradar_fusion_tracker_remove_from_track
    name: "🗑️ Release Flight Lock"
  - entity: button.skyradar_fusion_tracker_clear_additional_tracked
    name: "🧹 Wipe Target Registry"
```
